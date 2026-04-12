import datetime as dt
import hashlib
import hmac
import json
import asyncio

from typing import Mapping, Union

import httpx
import pytest
import pydantic

from sumup import AsyncSumup, Sumup
from sumup.types import Checkout
from sumup.webhooks import (
    DEFAULT_WEBHOOK_TOLERANCE,
    WEBHOOK_SIGNATURE_HEADER,
    WEBHOOK_SIGNATURE_VERSION,
    WEBHOOK_TIMESTAMP_HEADER,
    CheckoutCreatedEvent,
    WebhookEvent,
    WebhookHandler,
    WebhookSignatureError,
    WebhookSignatureExpiredError,
    WebhookTimestampError,
)


def test_verify_accepts_valid_signature() -> None:
    body = b'{"id":"evt_123","type":"checkout.created"}'
    now = dt.datetime(2026, 4, 12, 10, 0, tzinfo=dt.timezone.utc)
    headers = _sign_headers("wh_sec_test", now, body)

    handler = WebhookHandler(secret="wh_sec_test")

    handler.verify(headers, body, now=now)


def test_verify_rejects_expired_timestamp() -> None:
    body = b'{"id":"evt_123","type":"checkout.created"}'
    now = dt.datetime(2026, 4, 12, 10, 0, tzinfo=dt.timezone.utc)
    timestamp = now - DEFAULT_WEBHOOK_TOLERANCE - dt.timedelta(seconds=1)
    headers = _sign_headers("wh_sec_test", timestamp, body)

    handler = WebhookHandler(secret="wh_sec_test")

    with pytest.raises(WebhookSignatureExpiredError):
        handler.verify(headers, body, now=now)


def test_verify_rejects_invalid_signature() -> None:
    body = b'{"id":"evt_123","type":"checkout.created"}'
    now = dt.datetime(2026, 4, 12, 10, 0, tzinfo=dt.timezone.utc)
    headers = {
        WEBHOOK_TIMESTAMP_HEADER: str(int(now.timestamp())),
        WEBHOOK_SIGNATURE_HEADER: "v1=deadbeef",
    }

    handler = WebhookHandler(secret="wh_sec_test")

    with pytest.raises(WebhookSignatureError):
        handler.verify(headers, body, now=now)


def test_verify_rejects_missing_timestamp() -> None:
    handler = WebhookHandler(secret="wh_sec_test")

    with pytest.raises(WebhookTimestampError):
        handler.verify({WEBHOOK_SIGNATURE_HEADER: "v1=deadbeef"}, b"{}", now=_utc_now())


def test_parse_returns_typed_known_event() -> None:
    body = json.dumps(
        {
            "id": "evt_123",
            "type": "checkout.created",
            "created_at": "2026-04-11T10:00:00Z",
            "object": {
                "id": "chk_123",
                "type": "checkout",
                "url": "https://api.sumup.com/v0.1/checkouts/chk_123",
            },
        }
    )

    event = WebhookHandler(secret="wh_sec_test").parse(body)

    assert isinstance(event, CheckoutCreatedEvent)
    assert event.type.value == "checkout.created"


def test_parse_returns_generic_event_for_unknown_types() -> None:
    body = json.dumps(
        {
            "id": "evt_123",
            "type": "something.else",
            "created_at": "2026-04-11T10:00:00Z",
            "object": {
                "id": "obj_123",
                "type": "other",
                "url": "https://api.sumup.com/v0.1/other/obj_123",
            },
        }
    )

    event = WebhookHandler(secret="wh_sec_test").parse(body)

    assert type(event) is WebhookEvent
    assert event.type == "something.else"


def test_sumup_client_can_create_bound_webhook_handler() -> None:
    client = Sumup(api_key="test")

    handler = client.webhook_handler(secret="wh_sec_test")

    assert handler.secret == "wh_sec_test"
    assert handler._client is client._client

    client._client.close()


def test_async_sumup_client_can_create_bound_webhook_handler() -> None:
    client = AsyncSumup(api_key="test")

    handler = client.webhook_handler(secret="wh_sec_test")

    assert handler.secret == "wh_sec_test"
    assert handler._client is client._client

    asyncio.run(client._client.aclose())


def test_parse_rejects_invalid_json_payload() -> None:
    with pytest.raises(pydantic.ValidationError):
        WebhookHandler(secret="wh_sec_test").parse_and_verify(
            _sign_headers("wh_sec_test", _utc_now(), b"{"),
            b"{",
            now=_utc_now(),
        )


def test_parse_and_verify_binds_client_and_fetches_object(sdk_factory) -> None:
    checkout_payload = {
        "id": "chk_123",
        "amount": 10.0,
        "checkout_reference": "ref_123",
        "currency": "EUR",
        "date": "2026-04-11T10:00:00Z",
        "description": "Test payment",
        "idempotency_key": "idem_123",
        "merchant_code": "MC123",
        "status": "PENDING",
    }

    sdk = sdk_factory(
        lambda request: (
            _json_response(checkout_payload)
            if str(request.url) == "https://api.sumup.com/v0.1/checkouts/chk_123"
            else _json_response({"error": "not found"}, status_code=404)
        )
    )

    body = json.dumps(
        {
            "id": "evt_123",
            "type": "checkout.created",
            "created_at": "2026-04-11T10:00:00Z",
            "object": {
                "id": "chk_123",
                "type": "checkout",
                "url": "https://api.sumup.com/v0.1/checkouts/chk_123",
            },
        }
    )
    now = _utc_now()
    headers = _sign_headers("wh_sec_test", now, body.encode("utf-8"))
    handler = WebhookHandler(secret="wh_sec_test", client=sdk)

    event = handler.parse_and_verify(headers, body, now=now)
    assert isinstance(event, CheckoutCreatedEvent)
    checkout = event.fetch_object()

    assert isinstance(checkout, Checkout)
    assert checkout.id == "chk_123"


def test_parse_and_verify_binds_async_client_and_fetches_object_async() -> None:
    checkout_payload = {
        "id": "chk_123",
        "amount": 10.0,
        "checkout_reference": "ref_123",
        "currency": "EUR",
        "date": "2026-04-11T10:00:00Z",
        "description": "Test payment",
        "idempotency_key": "idem_123",
        "merchant_code": "MC123",
        "status": "PENDING",
    }

    async def transport_handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == "https://api.sumup.com/v0.1/checkouts/chk_123":
            return _json_response(checkout_payload)
        return _json_response({"error": "not found"}, status_code=404)

    sdk = AsyncSumup(api_key="test", base_url="https://api.sumup.test")
    original_client = sdk._client
    sdk._client = httpx.AsyncClient(
        base_url=original_client.base_url,
        timeout=original_client.timeout,
        headers=original_client.headers,
        transport=httpx.MockTransport(transport_handler),
    )
    asyncio.run(original_client.aclose())

    body = json.dumps(
        {
            "id": "evt_123",
            "type": "checkout.created",
            "created_at": "2026-04-11T10:00:00Z",
            "object": {
                "id": "chk_123",
                "type": "checkout",
                "url": "https://api.sumup.com/v0.1/checkouts/chk_123",
            },
        }
    )
    now = _utc_now()
    headers = _sign_headers("wh_sec_test", now, body.encode("utf-8"))
    webhook_handler = WebhookHandler(secret="wh_sec_test", client=sdk)

    try:
        event = webhook_handler.parse_and_verify(headers, body, now=now)
        assert isinstance(event, CheckoutCreatedEvent)
        checkout = asyncio.run(event.fetch_object_async())

        assert isinstance(checkout, Checkout)
        assert checkout.id == "chk_123"
    finally:
        asyncio.run(sdk._client.aclose())


def _sign_headers(secret: str, timestamp: dt.datetime, body: bytes) -> dict[str, str]:
    payload = f"{WEBHOOK_SIGNATURE_VERSION}:{int(timestamp.timestamp())}:".encode("utf-8") + body
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    return {
        WEBHOOK_TIMESTAMP_HEADER: str(int(timestamp.timestamp())),
        WEBHOOK_SIGNATURE_HEADER: f"{WEBHOOK_SIGNATURE_VERSION}={digest}",
    }


def _json_response(body: Mapping[str, Union[object, str, int, float]], status_code: int = 200):
    import httpx

    return httpx.Response(status_code, json=body)


def _utc_now() -> dt.datetime:
    return dt.datetime(2026, 4, 12, 10, 0, tzinfo=dt.timezone.utc)

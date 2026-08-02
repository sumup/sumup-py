import asyncio
import datetime as dt
import hashlib
import hmac
import json
from collections.abc import Callable
from typing import cast

import httpx
import pydantic
import pytest

from sumup import AsyncSumup, Sumup
from sumup.events import (
    DEFAULT_TOLERANCE,
    SIGNATURE_VERSION,
    EventHandlerRegistrationError,
    EventNotification,
    EventObjectUrlError,
    EventSignatureError,
    EventSignatureExpiredError,
    EventTimestampError,
    MemberUpdatedEvent,
    ReaderCreatedEvent,
    UnknownEvent,
    dangerously_parse_unverified_event_notification,
    parse_event_notification,
    verify_signature,
)
from sumup.types import Reader

_NOW = dt.datetime(2026, 4, 12, 10, 0, tzinfo=dt.timezone.utc)
_SECRET = "event_secret_test"


def test_parse_event_notification_verifies_and_returns_generated_event() -> None:
    body = _event_body("readers.created")
    signature, timestamp = _signature(_SECRET, _NOW, body)

    event = parse_event_notification(
        _SECRET,
        body,
        signature,
        timestamp,
        now=_NOW,
    )

    assert isinstance(event, ReaderCreatedEvent)
    assert event.type == "readers.created"


def test_dangerous_parse_returns_generated_and_unknown_events() -> None:
    known = dangerously_parse_unverified_event_notification(_event_body("members.updated"))
    unknown = dangerously_parse_unverified_event_notification(_event_body("merchant.updated"))

    assert isinstance(known, MemberUpdatedEvent)
    assert isinstance(unknown, UnknownEvent)
    assert unknown.type == "merchant.updated"


def test_verify_signature_rejects_invalid_and_expired_signatures() -> None:
    body = _event_body("readers.created")
    _, timestamp = _signature(_SECRET, _NOW, body)

    with pytest.raises(EventSignatureError):
        verify_signature(_SECRET, body, "v1=deadbeef", timestamp, now=_NOW)

    expired_at = _NOW - DEFAULT_TOLERANCE - dt.timedelta(seconds=1)
    signature, timestamp = _signature(_SECRET, expired_at, body)
    with pytest.raises(EventSignatureExpiredError):
        verify_signature(_SECRET, body, signature, timestamp, now=_NOW)


def test_verify_signature_rejects_missing_or_invalid_timestamp() -> None:
    body = _event_body("readers.created")

    with pytest.raises(EventTimestampError):
        verify_signature(_SECRET, body, "v1=deadbeef", "", now=_NOW)
    with pytest.raises(EventTimestampError):
        verify_signature(_SECRET, body, "v1=deadbeef", "not-a-timestamp", now=_NOW)


def test_events_handler_routes_registered_and_unhandled_events() -> None:
    client = Sumup(api_key="test")
    handled: list[tuple[str, Sumup]] = []
    unhandled: list[tuple[str, Sumup]] = []

    def fallback(event: EventNotification, callback_client: Sumup) -> None:
        unhandled.append((event.type, callback_client))

    def handle_reader(event: ReaderCreatedEvent, callback_client: Sumup) -> None:
        handled.append((event.type, callback_client))

    handler = client.events_handler(_SECRET, fallback)
    handler.on(ReaderCreatedEvent, handle_reader)

    try:
        _handle(handler.handle, _event_body("readers.created"))
        _handle(handler.handle, _event_body("members.updated"))
        _handle(handler.handle, _event_body("merchant.updated"))

        assert handled == [("readers.created", client)]
        assert unhandled == [("members.updated", client), ("merchant.updated", client)]
        assert handler.registered_event_types == ("readers.created",)
        assert handler.client is client
    finally:
        client._client.close()


def test_events_handler_verifies_before_dispatching() -> None:
    client = Sumup(api_key="test")
    calls: list[str] = []

    def fallback(event: EventNotification, _: Sumup) -> None:
        calls.append(event.type)

    handler = client.events_handler(_SECRET, fallback)
    body = _event_body("readers.created")
    _, timestamp = _signature(_SECRET, _NOW, body)

    try:
        with pytest.raises(EventSignatureError):
            handler.handle(body, "v1=deadbeef", timestamp, now=_NOW)
        assert calls == []
    finally:
        client._client.close()


def test_events_handler_rejects_unsupported_duplicate_and_late_registration() -> None:
    client = Sumup(api_key="test")
    handler = client.events_handler(_SECRET, lambda _event, _client: None)

    class CustomEvent(EventNotification):
        pass

    try:
        with pytest.raises(EventHandlerRegistrationError, match="generated event classes"):
            handler.on(CustomEvent, lambda _event, _client: None)

        handler.on(ReaderCreatedEvent, lambda _event, _client: None)
        with pytest.raises(EventHandlerRegistrationError, match="already registered"):
            handler.on(ReaderCreatedEvent, lambda _event, _client: None)

        _handle(handler.handle, _event_body("readers.created"))
        with pytest.raises(EventHandlerRegistrationError, match="handling has started"):
            handler.on(MemberUpdatedEvent, lambda _event, _client: None)
    finally:
        client._client.close()


def test_registered_event_can_fetch_its_object(sdk_factory) -> None:
    reader_payload = _reader_payload()
    object_url = "https://api.sumup.test/v0.1/merchants/MC0DE/readers/rdr_123"
    sdk = sdk_factory(
        lambda request: (
            _json_response(reader_payload)
            if str(request.url) == object_url
            else _json_response({"error": "not found"}, status_code=404)
        )
    )
    fetched: list[Reader] = []

    def handle_reader(event: ReaderCreatedEvent, _client: Sumup) -> None:
        fetched.append(event.fetch_object())

    handler = sdk.events_handler(_SECRET, lambda _event, _client: None)
    handler.on(ReaderCreatedEvent, handle_reader)

    _handle(handler.handle, _event_body("readers.created", object_url=object_url))

    assert len(fetched) == 1
    assert fetched[0].id == "rdr_123"


def test_fetch_object_rejects_urls_outside_the_client_host(sdk_factory) -> None:
    sdk = sdk_factory(lambda _request: _json_response(_reader_payload()))
    event = dangerously_parse_unverified_event_notification(
        _event_body("readers.created", object_url="https://example.com/readers/rdr_123"),
        client=sdk,
    )

    assert isinstance(event, ReaderCreatedEvent)
    with pytest.raises(EventObjectUrlError):
        event.fetch_object()


def test_async_events_handler_routes_and_fetches_generated_event() -> None:
    async def run() -> None:
        object_url = "https://api.sumup.test/v0.1/merchants/MC0DE/readers/rdr_123"

        async def transport(request: httpx.Request) -> httpx.Response:
            if str(request.url) == object_url:
                return _json_response(_reader_payload())
            return _json_response({"error": "not found"}, status_code=404)

        client = AsyncSumup(api_key="test", base_url="https://api.sumup.test")
        original_client = client._client
        client._client = httpx.AsyncClient(
            base_url=original_client.base_url,
            timeout=original_client.timeout,
            headers=original_client.headers,
            transport=httpx.MockTransport(transport),
        )
        await original_client.aclose()
        fetched: list[Reader] = []

        async def fallback(_event: EventNotification, _client: AsyncSumup) -> None:
            raise AssertionError("fallback should not be called")

        async def handle_reader(event: ReaderCreatedEvent, callback_client: AsyncSumup) -> None:
            assert callback_client is client
            fetched.append(await event.fetch_object_async())

        handler = client.events_handler(_SECRET, fallback)
        handler.on(ReaderCreatedEvent, handle_reader)
        body = _event_body("readers.created", object_url=object_url)
        signature, timestamp = _signature(_SECRET, _NOW, body)

        try:
            await handler.handle(body, signature, timestamp, now=_NOW)
        finally:
            await client._client.aclose()

        assert len(fetched) == 1
        assert fetched[0].id == "rdr_123"

    asyncio.run(run())


def test_event_parsing_requires_raw_bytes() -> None:
    with pytest.raises(TypeError, match="exact raw bytes"):
        dangerously_parse_unverified_event_notification(cast(bytes, "{}"))


def test_valid_signature_does_not_hide_invalid_json() -> None:
    body = b"{"
    signature, timestamp = _signature(_SECRET, _NOW, body)

    with pytest.raises(pydantic.ValidationError):
        parse_event_notification(_SECRET, body, signature, timestamp, now=_NOW)


def _handle(callback: Callable[..., None], body: bytes) -> None:
    signature, timestamp = _signature(_SECRET, _NOW, body)
    callback(body, signature, timestamp, now=_NOW)


def _event_body(
    event_type: str,
    *,
    object_url: str = "https://api.sumup.com/v0.1/objects/obj_123",
) -> bytes:
    return json.dumps(
        {
            "id": "evt_123",
            "type": event_type,
            "created_at": "2026-04-11T10:00:00Z",
            "object": {
                "id": "obj_123",
                "type": "reader" if event_type.startswith("readers.") else "member",
                "url": object_url,
            },
        }
    ).encode()


def _signature(secret: str, timestamp: dt.datetime, body: bytes) -> tuple[str, str]:
    timestamp_text = str(int(timestamp.timestamp()))
    payload = f"{SIGNATURE_VERSION}:{timestamp_text}:".encode() + body
    digest = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"{SIGNATURE_VERSION}={digest}", timestamp_text


def _reader_payload() -> dict[str, object]:
    return {
        "created_at": "2026-04-11T10:00:00Z",
        "device": {"identifier": "device_123", "model": "solo"},
        "id": "rdr_123",
        "name": "Front counter",
        "status": "paired",
        "updated_at": "2026-04-11T10:00:00Z",
    }


def _json_response(
    body: dict[str, object],
    status_code: int = 200,
) -> httpx.Response:
    return httpx.Response(status_code, json=body)

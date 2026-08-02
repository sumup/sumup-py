import asyncio
import hashlib
import hmac
import json

import httpx
import pytest

from sumup import APIError, AsyncSumup
from sumup.events import (
    EventCallbackError,
    EventHandlerRegistrationError,
    EventNotification,
    EventObjectUrlError,
    EventPayloadError,
    EventSignatureError,
    EventSignatureExpiredError,
    EventTimestampError,
    MemberCreatedEvent,
    MemberDeletedEvent,
    MemberUpdatedEvent,
    ReaderCreatedEvent,
    ReaderDeletedEvent,
    UnknownEvent,
    verify_event_signature,
)
from sumup.types import Reader

_NOW = 1788696000
_SECRET = "event_secret_test"
_URL = "https://api.sumup.test/v0.1/readers/rdr_123"


@pytest.fixture(autouse=True)
def fixed_clock(monkeypatch):
    monkeypatch.setattr("sumup._events.time.time", lambda: _NOW + 0.9)


@pytest.fixture
def sdk(sdk_factory):
    return sdk_factory(lambda _: httpx.Response(200, json=_reader()))


def _body(event_type="readers.created", *, url=_URL):
    return json.dumps(
        {
            "id": "evt_123",
            "type": event_type,
            "created_at": "2026-04-11T10:00:00Z",
            "object": {
                "id": "rdr_123",
                "type": "reader" if event_type.startswith("readers.") else "member",
                "url": url,
            },
        }
    ).encode()


def _signature(body, timestamp=str(_NOW), secret=_SECRET):
    digest = hmac.new(
        secret.encode(), f"v1:{timestamp}:".encode() + body, hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={digest}"


def _reader():
    return {
        "id": "rdr_123",
        "name": "Front counter",
        "status": "paired",
        "device": {"identifier": "device_123", "model": "solo"},
        "created_at": "2026-04-11T10:00:00Z",
        "updated_at": "2026-04-11T10:00:00Z",
    }


@pytest.mark.parametrize(
    "event_type,model",
    [
        ("members.created", MemberCreatedEvent),
        ("members.updated", MemberUpdatedEvent),
        ("members.deleted", MemberDeletedEvent),
        ("readers.created", ReaderCreatedEvent),
        ("readers.deleted", ReaderDeletedEvent),
        ("future.event", UnknownEvent),
    ],
)
def test_parse_event_notification(sdk, event_type, model):
    body = _body(event_type)
    for event in (
        sdk.parse_event_notification(body, _signature(body), _SECRET),
        sdk.parse_event_notification_without_verification(body),
    ):
        assert isinstance(event, model)
        assert event.type == event_type
        assert event.created_at.isoformat() == "2026-04-11T10:00:00+00:00"
        assert "_client" not in event.model_dump()
        assert "Bearer" not in repr(event)


@pytest.mark.parametrize(
    "body", [b'{ "name": "caf\xc3\xa9" }\n', bytearray(b"body"), memoryview(b"body"), "café"]
)
def test_verify_event_signature_preserves_raw_bytes(body):
    raw = body.encode() if isinstance(body, str) else bytes(body)
    verify_event_signature(_SECRET, body, _signature(raw))
    with pytest.raises(EventSignatureError):
        verify_event_signature(_SECRET, raw + b" ", _signature(raw))


def test_verify_event_signature_normalization():
    body = _body()
    signature = _signature(body, "0" + str(_NOW))
    timestamp, digest = signature.split(",v1=")
    verify_event_signature(_SECRET, body, " \t" + timestamp + ",v1=" + digest.upper() + "\r\n")
    with pytest.raises(EventSignatureError):
        verify_event_signature(_SECRET, body, signature.replace("t=0", "t="))


@pytest.mark.parametrize("offset", [-300, 300, 0])
def test_verify_event_signature_accepts_five_minute_boundary(offset):
    verify_event_signature(_SECRET, b"body", _signature(b"body", str(_NOW + offset)))


@pytest.mark.parametrize("offset", [-301, 301])
def test_verify_event_signature_rejects_expired_and_future(offset):
    with pytest.raises(EventSignatureExpiredError):
        verify_event_signature(_SECRET, b"body", _signature(b"body", str(_NOW + offset)))


@pytest.mark.parametrize(
    "header",
    [
        None,
        "",
        "v1=" + "a" * 64,
        "t=,v1=" + "a" * 64,
        "t=-1,v1=" + "a" * 64,
        "t=1.0,v1=" + "a" * 64,
        "t=١,v1=" + "a" * 64,
        "t=+1788696000,v1=" + "a" * 64,
        "t=" + "9" * 5000 + ",v1=" + "a" * 64,
        "t=9007199254740992,v1=" + "a" * 64,
        f"t={_NOW},v2=" + "a" * 64,
        f"t={_NOW},v1=abc",
        f"t={_NOW},v1=" + "x" * 64,
        f"t={_NOW}, v1=" + "a" * 64,
        f"t={_NOW},v1=" + "a" * 64 + ",v1=" + "b" * 64,
        f"t={_NOW},t={_NOW},v1=" + "a" * 64,
    ],
)
def test_verify_event_signature_rejects_malformed_header(header):
    with pytest.raises(EventSignatureError):
        verify_event_signature(_SECRET, b"body", header)


def test_invalid_timestamp_is_signature_error():
    with pytest.raises(EventTimestampError):
        verify_event_signature(_SECRET, b"body", "t=invalid,v1=abc")


@pytest.mark.parametrize("secret", ["", None, 123])
def test_signing_secret_is_required(sdk, secret):
    with pytest.raises(EventSignatureError):
        verify_event_signature(secret, b"body", _signature(b"body"))
    with pytest.raises(EventSignatureError):
        sdk.events_handler(secret, lambda _: None)


@pytest.mark.parametrize(
    "body", [{}, 12, None, [], b"\xff", b"{", b"[]", b"null", b"{}", b'{"x":NaN}']
)
def test_parse_rejects_invalid_payload(sdk, body):
    with pytest.raises(EventPayloadError):
        sdk.parse_event_notification_without_verification(body)


@pytest.mark.parametrize(
    "field,value",
    [
        ("id", ""),
        ("type", []),
        ("created_at", "2026-04-11"),
        ("created_at", "2026-04-11T10:00:00"),
        ("created_at", "2026-02-30T10:00:00Z"),
        ("object", None),
        ("object.id", ""),
        ("object.type", "member"),
        ("object.url", 123),
    ],
)
def test_parse_validates_envelope(sdk, field, value):
    payload = json.loads(_body())
    if "." in field:
        payload["object"][field.split(".")[1]] = value
    else:
        payload[field] = value
    with pytest.raises(EventPayloadError):
        sdk.parse_event_notification_without_verification(json.dumps(payload))


@pytest.mark.parametrize("created_at", [0, "1970-01-01T00:00:00Z", "1970-01-01 00:00:00+00:00"])
def test_parse_created_at_uses_datetime_parsing(sdk, created_at):
    payload = json.loads(_body())
    payload["created_at"] = created_at
    body = json.dumps(payload).encode()
    event = sdk.parse_event_notification(body, _signature(body), _SECRET)
    assert event.created_at.isoformat() == "1970-01-01T00:00:00+00:00"


def test_events_handler_dispatches_and_parse_does_not(sdk):
    calls = []
    handler = sdk.events_handler(_SECRET, lambda event: calls.append(("fallback", event.type)))

    @handler.on_reader_created
    def reader_created(event: ReaderCreatedEvent) -> None:
        calls.append(("reader", event.type))

    body = _body()
    assert isinstance(handler.parse(body, _signature(body)), ReaderCreatedEvent)
    assert calls == []
    for kind in ("readers.created", "members.updated", "future.event"):
        raw = _body(kind)
        handler.handle(raw, _signature(raw))
    assert calls == [
        ("reader", "readers.created"),
        ("fallback", "members.updated"),
        ("fallback", "future.event"),
    ]


def test_events_handler_verifies_before_parsing_or_dispatch(sdk):
    calls = []
    handler = sdk.events_handler(_SECRET, calls.append)
    with pytest.raises(EventSignatureError):
        handler.handle(b"not json", _signature(b"not json", secret="wrong"))
    with pytest.raises(EventPayloadError):
        handler.handle(b"not json", _signature(b"not json"))
    assert calls == []


def test_events_handler_registration_errors(sdk):
    with pytest.raises(EventHandlerRegistrationError):
        sdk.events_handler(_SECRET, None)
    handler = sdk.events_handler(_SECRET, lambda _: None)
    with pytest.raises(EventHandlerRegistrationError):
        handler.on_reader_created(None)
    handler.on_reader_created(lambda _: None)
    with pytest.raises(EventHandlerRegistrationError):
        handler.on_reader_created(lambda _: None)


@pytest.mark.parametrize("registered", [False, True])
def test_events_handler_chains_callback_errors(sdk, registered):
    error = RuntimeError("storage unavailable")

    def fail(_: EventNotification):
        raise error

    handler = sdk.events_handler(_SECRET, fail)
    if registered:
        handler.on_reader_created(fail)
    with pytest.raises(EventCallbackError) as raised:
        handler.handle(_body(), _signature(_body()))
    assert raised.value.__cause__ is error


def test_sync_handler_rejects_async_callback(sdk):
    async def callback(_: EventNotification):
        pass

    handler = sdk.events_handler(_SECRET, callback)
    with pytest.raises(EventCallbackError) as raised:
        handler.handle(_body(), _signature(_body()))
    assert isinstance(raised.value.__cause__, TypeError)


@pytest.mark.parametrize(
    "url",
    [
        "https://evil.test/reader",
        "http://api.sumup.test/reader",
        "https://api.sumup.test:444/reader",
        "/reader",
        "//evil.test/reader",
        "https://api.sumup.test@evil.test/reader",
        "https://[broken",
    ],
)
def test_fetch_object_checks_origin_before_request(sdk_factory, url):
    calls = []
    sdk = sdk_factory(lambda request: calls.append(request))
    event = sdk.parse_event_notification_without_verification(_body(url=url))
    with pytest.raises(EventObjectUrlError):
        event.fetch_object()
    assert calls == []


@pytest.mark.parametrize(
    "url,path",
    [
        (
            "https://user:pass@api.sumup.test/v0.1/readers/rdr_123?expand=true#ignored",
            "/prefix/v0.1/readers/rdr_123?expand=true",
        ),
        ("https://API.SUMUP.TEST:443//readers/rdr_123", "/prefix/readers/rdr_123"),
    ],
)
def test_fetch_object_normalizes_url_and_uses_client_options(sdk_factory, url, path):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json=_reader())

    sdk = sdk_factory(respond)
    sdk._client.base_url = "https://api.sumup.test/prefix"
    sdk._client.headers["X-Custom"] = "value"
    event = sdk.parse_event_notification_without_verification(_body(url=url))
    result = event.fetch_object()
    assert isinstance(result, Reader)
    assert result.name == "Front counter"
    assert len(requests) == 1
    request = requests[0]
    assert str(request.url) == "https://api.sumup.test" + path
    assert request.headers["Authorization"] == "Bearer test"
    assert request.headers["X-Custom"] == "value"


@pytest.mark.parametrize("status,body", [(404, {"title": "Not Found"}), (500, "unavailable")])
def test_fetch_object_preserves_api_errors(sdk_factory, status, body):
    sdk = sdk_factory(
        lambda _: httpx.Response(
            status, **({"json": body} if isinstance(body, dict) else {"text": body})
        )
    )
    event = sdk.parse_event_notification_without_verification(_body())
    with pytest.raises(APIError) as raised:
        event.fetch_object()
    assert raised.value.status == status
    assert raised.value.body == body


def test_fetch_object_does_not_follow_redirects(sdk_factory):
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(302, headers={"Location": "https://evil.test/reader"})

    sdk = sdk_factory(respond)
    sdk._client.follow_redirects = True
    event = sdk.parse_event_notification_without_verification(_body())
    with pytest.raises(APIError):
        event.fetch_object()
    assert len(requests) == 1


def test_async_events_handler_fetch_dispatch_errors_and_cancellation():
    async def run():
        sdk = AsyncSumup(api_key="test", base_url="https://api.sumup.test")
        await sdk._client.aclose()
        async with httpx.AsyncClient(
            base_url="https://api.sumup.test",
            transport=httpx.MockTransport(lambda _: httpx.Response(200, json=_reader())),
        ) as transport:
            sdk._client = transport
            calls = []

            async def fallback(event: EventNotification):
                await asyncio.sleep(0)
                calls.append(event.type)

            handler = sdk.events_handler(_SECRET, fallback)

            @handler.on_reader_created
            async def reader_created(event: ReaderCreatedEvent):
                reader = await event.fetch_object_async()
                calls.append(reader.id)

            assert isinstance(handler.parse(_body(), _signature(_body())), ReaderCreatedEvent)
            assert isinstance(
                sdk.parse_event_notification(_body(), _signature(_body()), _SECRET),
                ReaderCreatedEvent,
            )
            for kind in ("readers.created", "members.updated", "future.event"):
                raw = _body(kind)
                await handler.handle(raw, _signature(raw))
            assert calls == ["rdr_123", "members.updated", "future.event"]
            error = RuntimeError("storage unavailable")

            async def fail(_: EventNotification):
                raise error

            with pytest.raises(EventCallbackError) as raised:
                await sdk.events_handler(_SECRET, fail).handle(_body(), _signature(_body()))
            assert raised.value.__cause__ is error

            async def cancelled(_: EventNotification):
                raise asyncio.CancelledError

            with pytest.raises(asyncio.CancelledError):
                await sdk.events_handler(_SECRET, cancelled).handle(_body(), _signature(_body()))
            event = sdk.parse_event_notification_without_verification(_body())
            assert isinstance(event, ReaderCreatedEvent)
            with pytest.raises(TypeError, match="fetch_object_async"):
                event.fetch_object()

    asyncio.run(run())


def test_body_size_is_owned_by_receiver():
    body = b"x" * (2 * 1024 * 1024)
    verify_event_signature(_SECRET, body, _signature(body))


def test_public_surface_has_no_tolerance_or_separate_timestamp():
    import inspect

    from sumup import events

    assert "DEFAULT_TOLERANCE" not in events.__all__
    assert "TIMESTAMP_HEADER" not in events.__all__
    assert "FetchableEvent" not in events.__all__
    assert list(inspect.signature(verify_event_signature).parameters) == [
        "secret",
        "body",
        "signature",
    ]


def test_parse_rejects_non_json_constants_in_otherwise_valid_event(sdk):
    body = _body()[:-1] + b', "extra": NaN}'
    with pytest.raises(EventPayloadError):
        sdk.parse_event_notification_without_verification(body)


@pytest.mark.parametrize(
    "method,event_type,model",
    [
        ("on_member_created", "members.created", MemberCreatedEvent),
        ("on_member_deleted", "members.deleted", MemberDeletedEvent),
        ("on_member_updated", "members.updated", MemberUpdatedEvent),
        ("on_reader_created", "readers.created", ReaderCreatedEvent),
        ("on_reader_deleted", "readers.deleted", ReaderDeletedEvent),
    ],
)
def test_specific_registration_preserves_callback_and_dispatches(sdk, method, event_type, model):
    calls = []
    handler = sdk.events_handler(_SECRET, lambda _: pytest.fail("unexpected fallback"))

    def callback(event: EventNotification) -> None:
        calls.append(event)

    register = getattr(handler, method)
    assert register(callback) is callback
    body = _body(event_type)
    handler.handle(body, _signature(body))
    assert len(calls) == 1
    assert isinstance(calls[0], model)
    with pytest.raises(EventHandlerRegistrationError):
        register(callback)


@pytest.mark.parametrize(
    "method,event_type,model",
    [
        ("on_member_created", "members.created", MemberCreatedEvent),
        ("on_member_deleted", "members.deleted", MemberDeletedEvent),
        ("on_member_updated", "members.updated", MemberUpdatedEvent),
        ("on_reader_created", "readers.created", ReaderCreatedEvent),
        ("on_reader_deleted", "readers.deleted", ReaderDeletedEvent),
    ],
)
def test_async_specific_registration_preserves_callback_and_dispatches(method, event_type, model):
    async def run():
        sdk = AsyncSumup(api_key="test")
        try:
            calls = []

            async def fallback(_: EventNotification) -> None:
                pytest.fail("unexpected fallback")

            async def callback(event: EventNotification) -> None:
                await asyncio.sleep(0)
                calls.append(event)

            handler = sdk.events_handler(_SECRET, fallback)
            register = getattr(handler, method)
            with pytest.raises(EventHandlerRegistrationError):
                register(None)
            assert register(callback) is callback
            body = _body(event_type)
            await handler.handle(body, _signature(body))
            assert len(calls) == 1
            assert isinstance(calls[0], model)
            with pytest.raises(EventHandlerRegistrationError):
                register(callback)
        finally:
            await sdk._client.aclose()

    asyncio.run(run())


def test_decorated_callback_remains_directly_callable(sdk):
    calls = []
    handler = sdk.events_handler(_SECRET, lambda _: None)

    @handler.on_reader_created
    def callback(notification: ReaderCreatedEvent) -> None:
        calls.append(notification.id)

    event = sdk.parse_event_notification_without_verification(_body())
    assert isinstance(event, ReaderCreatedEvent)
    # Keeping the parameter name also checks that the decorator preserves typing.
    callback(notification=event)
    assert calls == [event.id]

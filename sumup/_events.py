"""Verification and dispatch for SumUp event notifications."""

from __future__ import annotations

import hashlib
import hmac
import inspect
import json
import re
import time
from collections.abc import Awaitable, Callable
from typing import Annotated, ClassVar, Generic, TypeVar, cast

import httpx
import pydantic

from ._exceptions import APIError, SumupError

SIGNATURE_HEADER = "X-SumUp-Webhook-Signature"
"""Header containing the signing timestamp and signature. Pass its complete value."""
_TOLERANCE_SECONDS = 300
EventBody = str | bytes | bytearray | memoryview
"""Unchanged request bytes or a UTF-8 string, as returned by your web framework.

Read the body before JSON middleware. Parsing and reserializing can change the
signed bytes and cause verification to fail.
"""
_NonemptyString = Annotated[str, pydantic.Field(strict=True, min_length=1)]
_ObjectT = TypeVar("_ObjectT", bound=pydantic.BaseModel)


class EventError(SumupError):
    """Base class for event configuration, verification, parsing, and callback errors."""


class EventSignatureError(EventError):
    """Missing signing secret, invalid signature, or invalid signing timestamp."""


class EventTimestampError(EventSignatureError):
    """Missing or malformed signing timestamp in the signature header."""


class EventSignatureExpiredError(EventSignatureError):
    """Signing timestamp more than five minutes before or after the receiver's clock."""


class EventPayloadError(EventError):
    """Invalid UTF-8, JSON, or notification envelope."""


class EventCallbackError(EventError):
    """The selected callback raised an exception or used the wrong sync/async interface.

    The original exception is available as __cause__. Return a 5xx HTTP response
    on processing failure to allow the sender to retry the delivery.
    """


class EventHandlerRegistrationError(EventError):
    """Invalid or duplicate event callback registration."""


class EventObjectUrlError(EventError):
    """The resource URL is malformed or differs from the configured API origin.

    The scheme, host, and port must match the API client's base URL.
    """


class EventObject(pydantic.BaseModel):
    """Reference to the resource associated with an event.

    Attributes:
        id: Identifier of the referenced resource.
        type: Resource type, such as "member" or "reader".
        url: API URL used by the event's fetch_object() or fetch_object_async().
    """

    id: _NonemptyString
    type: _NonemptyString
    url: _NonemptyString


class EventNotification(pydantic.BaseModel):
    """Metadata shared by known events and UnknownEvent.

    Notifications contain a resource reference. Known event classes provide
    fetch_object() and fetch_object_async() to retrieve its current state.

    Attributes:
        id: Event identifier. Use it to recognize repeated deliveries.
        type: Event name, such as "members.updated".
        created_at: Time the event was created, as a timezone-aware datetime.
            Signature verification checks the header's signing timestamp instead.
        object: Reference to the associated API resource.
    """

    id: _NonemptyString
    type: _NonemptyString
    created_at: pydantic.AwareDatetime
    object: EventObject

    _client: httpx.Client | httpx.AsyncClient | None = pydantic.PrivateAttr(default=None)
    _object_type: ClassVar[str | None] = None

    @pydantic.field_validator("object")
    @classmethod
    def _validate_object(cls, value: EventObject) -> EventObject:
        if cls._object_type is not None and value.type != cls._object_type:
            raise ValueError("event object type does not match its notification type")
        return value


class UnknownEvent(EventNotification):
    """A valid notification whose type is not recognized by this SDK version.

    Handlers send it to the fallback callback. Its id, type, created_at, and object
    remain available, but it has no typed resource-fetching method.
    """


class FetchableEvent(EventNotification, Generic[_ObjectT]):
    """Base for known events with typed resource fetching."""

    EVENT_TYPE: ClassVar[str]
    _response_model: ClassVar[type[pydantic.BaseModel]]

    def _parse_response(self, response: httpx.Response) -> _ObjectT:
        if not response.is_success:
            try:
                body = response.json()
            except ValueError:
                body = response.text
            raise APIError("Unable to fetch event object", status=response.status_code, body=body)
        return cast(_ObjectT, self._response_model.model_validate_json(response.content))

    def fetch_object(self) -> _ObjectT:
        """Fetch the latest state of this event's resource.

        Uses the Sumup client that parsed the event, including its authentication and
        request settings. The result reflects the resource at fetch time, which may
        have changed since the event was created. A deleted resource may return 404.

        The resource URL must match the client's scheme, host, and port. Its path and
        query are appended to the configured base URL; URL credentials and fragments
        are ignored. Redirects are not followed.

        Returns:
            The resource model associated with this event, such as Member or Reader.

        Raises:
            EventObjectUrlError: The resource URL is invalid or uses another API origin.
            APIError: The API returns a non-2xx response; status and body are available.
            EventError: The event was not parsed with an API client.
            TypeError: The event belongs to AsyncSumup; use fetch_object_async().

        HTTPX transport errors and Pydantic response-validation errors propagate.
        """
        if self._client is None:
            raise EventError("event notification is not bound to a SumUp client")
        if not isinstance(self._client, httpx.Client):
            raise TypeError("use fetch_object_async() with an AsyncSumup client")
        response = self._client.get(
            _validated_object_url(self._client, self.object.url), follow_redirects=False
        )
        return self._parse_response(response)

    async def fetch_object_async(self) -> _ObjectT:
        """Asynchronously fetch the latest state of this event's resource.

        Uses the AsyncSumup client that parsed the event. Await this method inside
        async callbacks. Like fetch_object(), it returns current state, checks the
        API origin, and does not follow redirects. Deleted resources may return 404.

        Returns:
            The resource model associated with this event, such as Member or Reader.

        Raises:
            EventObjectUrlError: The resource URL is invalid or uses another API origin.
            APIError: The API returns a non-2xx response; status and body are available.
            EventError: The event was not parsed with an API client.
            TypeError: The event belongs to Sumup; use fetch_object().

        HTTPX transport errors and Pydantic response-validation errors propagate.
        """
        if self._client is None:
            raise EventError("event notification is not bound to a SumUp client")
        if not isinstance(self._client, httpx.AsyncClient):
            raise TypeError("use fetch_object() with a Sumup client")
        response = await self._client.get(
            _validated_object_url(self._client, self.object.url), follow_redirects=False
        )
        return self._parse_response(response)


EventCallback = Callable[[EventNotification], None]
"""Synchronous fallback receiving one event. Return None on success or raise on failure."""
AsyncEventCallback = Callable[[EventNotification], Awaitable[None]]
"""Async fallback receiving one event. Failures are wrapped in EventCallbackError."""
_ErasedCallback = Callable[[EventNotification], object]


class _BaseEventsHandler:
    def __init__(
        self, *, secret: str, fallback: _ErasedCallback, client: httpx.Client | httpx.AsyncClient
    ) -> None:
        _assert_secret(secret)
        if not callable(fallback):
            raise EventHandlerRegistrationError("an event fallback callback is required")
        self._secret = secret
        self._fallback = fallback
        self._client = client
        self._callbacks: dict[str, _ErasedCallback] = {}

    def _register(self, event_type: str, callback: _ErasedCallback) -> None:
        if not callable(callback):
            raise EventHandlerRegistrationError("an event callback is required")
        if event_type in self._callbacks:
            raise EventHandlerRegistrationError(f"callback already registered for {event_type}")
        self._callbacks[event_type] = callback

    def parse(self, body: EventBody, signature: str | None) -> EventNotification:
        """Verify and parse an incoming event without running callbacks.

        Performs no network requests. Even on AsyncEventsHandler, this method is
        synchronous and does not need to be awaited.

        Args:
            body: Unchanged request bytes or a UTF-8 string, read before JSON parsing.
            signature: Complete X-SumUp-Webhook-Signature header value. None is accepted
                for framework compatibility but raises EventSignatureError.

        Returns:
            A typed event bound to this handler's client, or UnknownEvent for a new type.

        Raises:
            EventSignatureError: Verification fails, including a signing timestamp more
                than five minutes before or after the receiver's clock.
            EventPayloadError: The body is not raw input, or its UTF-8, JSON, or event
                fields are invalid.
        """
        return parse_event_notification(self._secret, body, signature, client=self._client)


class _SyncEventsHandler(_BaseEventsHandler):
    def handle(self, body: EventBody, signature: str | None) -> None:
        """Verify an event and run its registered callback or the fallback.

        Callbacks run only after verification and parsing succeed. This method waits
        for the callback to finish; it does not send an HTTP response. Acknowledge with
        2xx after success, reject invalid input with 400, and return 5xx on callback
        failure so the sender can retry. Make callback side effects idempotent.

        Args:
            body: Unchanged request bytes or a UTF-8 string, read before JSON parsing.
                Your server owns reading the body and enforcing its size limit.
            signature: Complete X-SumUp-Webhook-Signature header value. None or an empty
                value fails verification.

        Raises:
            EventSignatureError: Invalid signature or signing timestamp, including the
                fixed five-minute window before or after the receiver's clock.
            EventPayloadError: Invalid raw input, UTF-8, JSON, or event fields.
            EventCallbackError: The callback failed; __cause__ holds its exception.
        """
        event = self.parse(body, signature)
        callback = self._callbacks.get(event.type, self._fallback)
        try:
            result = callback(event)
            if inspect.isawaitable(result):
                if inspect.iscoroutine(result):
                    result.close()
                raise TypeError("use AsyncSumup.events_handler() for async callbacks")
        except Exception as cause:
            raise EventCallbackError("event callback failed") from cause


class _AsyncEventsHandler(_BaseEventsHandler):
    async def handle(self, body: EventBody, signature: str | None) -> None:
        """Verify an event and await its registered callback or the fallback.

        Callbacks run only after verification and parsing succeed. Await completion
        before sending a 2xx HTTP response. Reject invalid input with 400; return 5xx
        on callback failure so the sender can retry. Make side effects idempotent.
        Cancellation propagates to the caller without being wrapped.

        Args:
            body: Unchanged request bytes or a UTF-8 string, read before JSON parsing.
                Your server owns reading the body and enforcing its size limit.
            signature: Complete X-SumUp-Webhook-Signature header value. None or an empty
                value fails verification.

        Raises:
            EventSignatureError: Invalid signature or signing timestamp, including the
                fixed five-minute window before or after the receiver's clock.
            EventPayloadError: Invalid raw input, UTF-8, JSON, or event fields.
            EventCallbackError: The callback failed; __cause__ holds its exception.
        """
        event = self.parse(body, signature)
        callback = self._callbacks.get(event.type, self._fallback)
        try:
            await cast(Awaitable[None], callback(event))
        except Exception as cause:
            raise EventCallbackError("event callback failed") from cause


def verify_event_signature(secret: str, body: EventBody, signature: str | None) -> None:
    """Verify a delivery's signature and signing timestamp without parsing JSON.

    Useful before storing a delivery in a trusted queue. Workers can later use
    client.parse_event_notification_without_verification() on the stored body.
    This function performs no network requests and does not validate event fields.

    Args:
        secret: Event signing secret. This is separate from your API key.
        body: Unchanged request bytes or a UTF-8 string. Do not parse and reserialize.
        signature: Complete X-SumUp-Webhook-Signature header value, including its
            timestamp. None is accepted for framework compatibility but fails
            verification.

    Raises:
        EventSignatureError: The secret is missing, the signature is invalid, or the
            signing timestamp is more than five minutes before or after the
            receiver's clock.
        EventPayloadError: The body is not bytes or a valid UTF-8 string.
    """
    _verify_bytes(secret, _body_bytes(body), signature)


def _assert_secret(secret: str) -> None:
    if not isinstance(secret, str) or not secret:
        raise EventSignatureError("event signing secret is required")


def _verify_bytes(secret: str, body: bytes, signature: str | None) -> None:
    _assert_secret(secret)
    if not isinstance(signature, str) or not signature.strip():
        raise EventSignatureError("missing event signature header")
    timestamp_field, separator, signature_field = signature.strip().partition(",")
    if not timestamp_field.startswith("t="):
        raise EventTimestampError("missing signing timestamp")
    timestamp_text = timestamp_field[2:]
    if not re.fullmatch(r"[0-9]+", timestamp_text):
        raise EventTimestampError("invalid signing timestamp")
    try:
        timestamp = int(timestamp_text)
    except ValueError as cause:
        raise EventTimestampError("invalid signing timestamp") from cause
    if timestamp > 2**53 - 1:
        raise EventTimestampError("invalid signing timestamp")
    if abs(int(time.time()) - timestamp) > _TOLERANCE_SECONDS:
        raise EventSignatureExpiredError("event timestamp outside the five-minute window")
    if not separator or not re.fullmatch(r"v1=[0-9a-fA-F]{64}", signature_field):
        raise EventSignatureError("invalid event signature header")
    # Preserve the timestamp's original spelling and the exact request bytes.
    expected = hmac.digest(
        secret.encode("utf-8"),
        b"v1:" + timestamp_text.encode("ascii") + b":" + body,
        hashlib.sha256,
    )
    if not hmac.compare_digest(expected, bytes.fromhex(signature_field[3:])):
        raise EventSignatureError("invalid event signature")


def parse_event_notification(
    secret: str, body: EventBody, signature: str | None, *, client: httpx.Client | httpx.AsyncClient
) -> EventNotification:
    raw = _body_bytes(body)
    _verify_bytes(secret, raw, signature)
    return _parse(raw, client)


def parse_event_notification_without_verification(
    body: EventBody, *, client: httpx.Client | httpx.AsyncClient
) -> EventNotification:
    return _parse(_body_bytes(body), client)


def _parse(body: bytes, client: httpx.Client | httpx.AsyncClient) -> EventNotification:
    from .events import _EVENT_MODELS

    try:
        payload = json.loads(body.decode("utf-8"), parse_constant=_reject_json_constant)
        if not isinstance(payload, dict):
            raise EventPayloadError("expected an event object")
        event_type = payload.get("type")
        model = (
            _EVENT_MODELS.get(event_type, UnknownEvent)
            if isinstance(event_type, str)
            else UnknownEvent
        )
        event = model.model_validate(payload)
    except (ValueError, RecursionError) as cause:
        raise EventPayloadError("invalid event JSON, UTF-8, or notification envelope") from cause
    event._client = client
    return event


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"invalid JSON constant: {value}")


def _body_bytes(body: EventBody) -> bytes:
    if isinstance(body, str):
        try:
            return body.encode("utf-8")
        except UnicodeError as cause:
            raise EventPayloadError("invalid UTF-8 event body") from cause
    if isinstance(body, (bytes, bytearray, memoryview)):
        return bytes(body)
    raise EventPayloadError("expected raw request bytes or a string, not parsed JSON")


def _validated_object_url(client: httpx.Client | httpx.AsyncClient, value: str) -> httpx.URL:
    try:
        url = httpx.URL(value)
    except (httpx.InvalidURL, ValueError) as cause:
        raise EventObjectUrlError("invalid event object URL") from cause
    base = client.base_url
    if url.scheme not in ("https", "http") or (url.scheme, url.host, url.port) != (
        base.scheme,
        base.host,
        base.port,
    ):
        raise EventObjectUrlError("event object URL must use the configured API origin")
    return base.copy_with(
        raw_path=base.raw_path.split(b"?", 1)[0].rstrip(b"/") + b"/" + url.raw_path.lstrip(b"/"),
        fragment=None,
    )

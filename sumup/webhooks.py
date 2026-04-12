from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import os
from enum import Enum
from typing import Any, ClassVar, Generic, Mapping, Type, TypeVar, Union, cast

import httpx
import pydantic

from ._exceptions import APIError, SumupError
from .types import Checkout, Member

WEBHOOK_SIGNATURE_HEADER = "X-SumUp-Webhook-Signature"
WEBHOOK_TIMESTAMP_HEADER = "X-SumUp-Webhook-Timestamp"
WEBHOOK_SIGNATURE_VERSION = "v1"
DEFAULT_WEBHOOK_TOLERANCE = dt.timedelta(minutes=5)
WEBHOOK_SECRET_ENV_VAR = "SUMUP_WEBHOOK_SECRET"

_UTC = dt.timezone.utc
_ClientT = TypeVar("_ClientT", httpx.Client, httpx.AsyncClient)
_BodyT = Union[bytes, bytearray, memoryview, str]
_ResponseT = TypeVar("_ResponseT", bound=pydantic.BaseModel)


class WebhookError(SumupError):
    """Base class for webhook parsing and verification failures."""


class WebhookSecretMissingError(WebhookError):
    """Raised when webhook verification is attempted without a configured secret."""


class WebhookTimestampError(WebhookError):
    """Raised when the webhook timestamp header is missing or malformed."""


class WebhookSignatureError(WebhookError):
    """Raised when the webhook signature is missing or invalid."""


class WebhookSignatureExpiredError(WebhookSignatureError):
    """Raised when the webhook timestamp is outside the allowed tolerance window."""


class WebhookEventType(str, Enum):
    """Known SumUp webhook event type strings."""

    CHECKOUT_CREATED = "checkout.created"
    CHECKOUT_PROCESSED = "checkout.processed"
    CHECKOUT_FAILED = "checkout.failed"
    CHECKOUT_TERMINATED = "checkout.terminated"
    MEMBER_CREATED = "member.created"
    MEMBER_REMOVED = "member.removed"


class WebhookObject(pydantic.BaseModel):
    """Reference to the SumUp resource associated with a webhook event."""

    id: str
    type: str
    url: str


class WebhookEvent(pydantic.BaseModel):
    """Generic SumUp webhook event envelope."""

    id: str
    type: str
    created_at: dt.datetime
    object: WebhookObject

    _client: httpx.Client | httpx.AsyncClient | None = pydantic.PrivateAttr(default=None)

    def bind_client(self, client: object | None) -> WebhookEvent:
        """Attach a SumUp or HTTPX client used by fetchable event helpers."""
        self._client = _unwrap_client(client)
        return self


class _FetchableEvent(WebhookEvent, Generic[_ResponseT]):
    _response_model: ClassVar[Type[pydantic.BaseModel]]

    def _require_sync_client(self) -> httpx.Client:
        if self._client is None:
            raise RuntimeError("webhook event is not bound to a SumUp client")
        if not isinstance(self._client, httpx.Client):
            raise RuntimeError(
                "webhook event is bound to an async client; use fetch_object_async()"
            )
        return self._client

    def _require_async_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("webhook event is not bound to a SumUp client")
        if not isinstance(self._client, httpx.AsyncClient):
            raise RuntimeError("webhook event is bound to a sync client; use fetch_object()")
        return self._client

    def _parse_response(self, response: httpx.Response) -> _ResponseT:
        if response.status_code != 200:
            raise APIError("Unexpected response", status=response.status_code, body=response.text)
        return cast(_ResponseT, self._response_model.model_validate(response.json()))

    def fetch_object(self) -> _ResponseT:
        """Fetch the resource referenced by this event using a bound sync client."""
        response = self._require_sync_client().get(self.object.url)
        return self._parse_response(response)

    async def fetch_object_async(self) -> _ResponseT:
        """Fetch the resource referenced by this event using a bound async client."""
        response = await self._require_async_client().get(self.object.url)
        return self._parse_response(response)


class CheckoutCreatedEvent(_FetchableEvent[Checkout]):
    """Event emitted when a checkout is created."""

    _response_model: ClassVar[Type[pydantic.BaseModel]] = Checkout
    type: pydantic.SerializeAsAny[WebhookEventType] = WebhookEventType.CHECKOUT_CREATED


class CheckoutProcessedEvent(_FetchableEvent[Checkout]):
    """Event emitted when a checkout is processed."""

    _response_model: ClassVar[Type[pydantic.BaseModel]] = Checkout
    type: pydantic.SerializeAsAny[WebhookEventType] = WebhookEventType.CHECKOUT_PROCESSED


class CheckoutFailedEvent(_FetchableEvent[Checkout]):
    """Event emitted when a checkout processing attempt fails."""

    _response_model: ClassVar[Type[pydantic.BaseModel]] = Checkout
    type: pydantic.SerializeAsAny[WebhookEventType] = WebhookEventType.CHECKOUT_FAILED


class CheckoutTerminatedEvent(_FetchableEvent[Checkout]):
    """Event emitted when a checkout is terminated."""

    _response_model: ClassVar[Type[pydantic.BaseModel]] = Checkout
    type: pydantic.SerializeAsAny[WebhookEventType] = WebhookEventType.CHECKOUT_TERMINATED


class MemberCreatedEvent(_FetchableEvent[Member]):
    """Event emitted when a merchant member is created."""

    _response_model: ClassVar[Type[pydantic.BaseModel]] = Member
    type: pydantic.SerializeAsAny[WebhookEventType] = WebhookEventType.MEMBER_CREATED


class MemberRemovedEvent(_FetchableEvent[Member]):
    """Event emitted when a merchant member is removed."""

    _response_model: ClassVar[Type[pydantic.BaseModel]] = Member
    type: pydantic.SerializeAsAny[WebhookEventType] = WebhookEventType.MEMBER_REMOVED


KnownWebhookEvent = Union[
    CheckoutCreatedEvent,
    CheckoutProcessedEvent,
    CheckoutFailedEvent,
    CheckoutTerminatedEvent,
    MemberCreatedEvent,
    MemberRemovedEvent,
]
WebhookNotification = Union[KnownWebhookEvent, WebhookEvent]


class WebhookHandler:
    """Verify and parse incoming SumUp webhook requests."""

    def __init__(
        self,
        *,
        secret: str | None = None,
        tolerance: dt.timedelta = DEFAULT_WEBHOOK_TOLERANCE,
        client: object | None = None,
    ) -> None:
        self.secret = secret or os.getenv(WEBHOOK_SECRET_ENV_VAR)
        self.tolerance = tolerance
        self._client = _unwrap_client(client)

    def verify(
        self,
        headers: Mapping[str, str],
        body: _BodyT,
        *,
        now: dt.datetime | None = None,
    ) -> None:
        """Verify the webhook signature and timestamp headers for a payload."""
        if not self.secret:
            raise WebhookSecretMissingError(
                f"webhook secret is not configured; pass secret=... or set {WEBHOOK_SECRET_ENV_VAR}"
            )

        signature = _get_header(headers, WEBHOOK_SIGNATURE_HEADER)
        if not signature:
            raise WebhookSignatureError("missing webhook signature header")

        timestamp_text = _get_header(headers, WEBHOOK_TIMESTAMP_HEADER)
        if not timestamp_text:
            raise WebhookTimestampError("missing webhook timestamp header")

        try:
            timestamp = dt.datetime.fromtimestamp(int(timestamp_text), tz=_UTC)
        except (TypeError, ValueError) as exc:
            raise WebhookTimestampError("invalid webhook timestamp") from exc

        if abs(_coerce_now(now) - timestamp) > self.tolerance:
            raise WebhookSignatureExpiredError("webhook timestamp outside allowed tolerance")

        version, separator, digest = signature.partition("=")
        if separator != "=" or not version or not digest:
            raise WebhookSignatureError("invalid webhook signature format")
        if version != WEBHOOK_SIGNATURE_VERSION:
            raise WebhookSignatureError("unsupported webhook signature version")

        expected = hmac.new(
            self.secret.encode("utf-8"),
            _signed_content(timestamp, body),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, digest):
            raise WebhookSignatureError("invalid webhook signature")

    def parse(self, body: _BodyT) -> WebhookNotification:
        """Parse a webhook payload into the most specific known event model."""
        payload = _load_json(body)
        event_type = payload.get("type")
        if isinstance(event_type, str):
            model = _EVENT_TYPES.get(event_type, WebhookEvent)
        else:
            model = WebhookEvent
        event = model.model_validate(payload)
        return event.bind_client(self._client)

    def parse_and_verify(
        self,
        headers: Mapping[str, str],
        body: _BodyT,
        *,
        now: dt.datetime | None = None,
    ) -> WebhookNotification:
        """Verify a webhook request and then parse it into an event model."""
        self.verify(headers, body, now=now)
        return self.parse(body)


_EVENT_TYPES: dict[str, type[WebhookEvent]] = {
    WebhookEventType.CHECKOUT_CREATED.value: CheckoutCreatedEvent,
    WebhookEventType.CHECKOUT_PROCESSED.value: CheckoutProcessedEvent,
    WebhookEventType.CHECKOUT_FAILED.value: CheckoutFailedEvent,
    WebhookEventType.CHECKOUT_TERMINATED.value: CheckoutTerminatedEvent,
    WebhookEventType.MEMBER_CREATED.value: MemberCreatedEvent,
    WebhookEventType.MEMBER_REMOVED.value: MemberRemovedEvent,
}


def _unwrap_client(client: object | None) -> httpx.Client | httpx.AsyncClient | None:
    if client is None:
        return None
    if isinstance(client, (httpx.Client, httpx.AsyncClient)):
        return client

    inner_client = getattr(client, "_client", None)
    if isinstance(inner_client, (httpx.Client, httpx.AsyncClient)):
        return inner_client

    raise TypeError("client must be a Sumup client, httpx.Client, or httpx.AsyncClient")


def _coerce_now(now: dt.datetime | None) -> dt.datetime:
    if now is None:
        return dt.datetime.now(tz=_UTC)
    if now.tzinfo is None:
        return now.replace(tzinfo=_UTC)
    return now.astimezone(_UTC)


def _coerce_body_bytes(body: _BodyT) -> bytes:
    if isinstance(body, bytes):
        return body
    if isinstance(body, str):
        return body.encode("utf-8")
    return bytes(body)


def _load_json(body: _BodyT) -> dict[str, Any]:
    return pydantic.TypeAdapter(dict[str, Any]).validate_json(_coerce_body_bytes(body))


def _get_header(headers: Mapping[str, str], name: str) -> str | None:
    value = headers.get(name)
    if value is not None:
        return value

    target = name.lower()
    for key, header_value in headers.items():
        if key.lower() == target:
            return header_value
    return None


def _signed_content(timestamp: dt.datetime, body: _BodyT) -> bytes:
    return f"{WEBHOOK_SIGNATURE_VERSION}:{int(timestamp.timestamp())}:".encode(
        "utf-8"
    ) + _coerce_body_bytes(body)


__all__ = [
    "DEFAULT_WEBHOOK_TOLERANCE",
    "WEBHOOK_SECRET_ENV_VAR",
    "WEBHOOK_SIGNATURE_HEADER",
    "WEBHOOK_SIGNATURE_VERSION",
    "WEBHOOK_TIMESTAMP_HEADER",
    "CheckoutCreatedEvent",
    "CheckoutFailedEvent",
    "CheckoutProcessedEvent",
    "CheckoutTerminatedEvent",
    "KnownWebhookEvent",
    "MemberCreatedEvent",
    "MemberRemovedEvent",
    "WebhookError",
    "WebhookEvent",
    "WebhookEventType",
    "WebhookHandler",
    "WebhookNotification",
    "WebhookObject",
    "WebhookSecretMissingError",
    "WebhookSignatureError",
    "WebhookSignatureExpiredError",
    "WebhookTimestampError",
]

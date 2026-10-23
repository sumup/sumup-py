from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import httpx
import pydantic


def _error_message(body: object) -> str | None:
    if not isinstance(body, pydantic.BaseModel):
        return None
    for field in ("detail", "details", "message", "error_message", "title"):
        message = getattr(body, field, None)
        if isinstance(message, str) and message:
            return message
    return _error_message(getattr(body, "errors", None))


class SumupError(Exception):
    """Base class for SumUp SDK errors."""


class APIError(SumupError):
    """Base class for API response, connection, and timeout errors."""

    message: str
    """A readable description of the failure."""

    status: int | None
    body: object | None

    """The response body, parsed into its documented type when available.

    Documented JSON errors use the generated Pydantic models, including arrays and
    unions. Responses with the application/problem+json media type use Problem
    when no documented type is available. Other unexpected responses or bodies
    that do not match their type retain decoded JSON. Invalid JSON and empty
    responses are preserved as text.

    A JSON null response or an error constructed without a body has a value of None.
    """

    response: httpx.Response | None
    """The original HTTP response, or None when constructed without one."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        body: object | None = None,
        response: httpx.Response | None = None,
    ) -> None:
        bodies = body if isinstance(body, list) else [body]
        messages = [text for item in bodies if (text := _error_message(item))]
        self.message = "; ".join(messages) or message
        super().__init__(self.message)
        self.status = status
        self.body = body
        self.response = response

    def __str__(self) -> str:
        return f"HTTP {self.status}: {self.message}" if self.status is not None else self.message

    @staticmethod
    def from_response(
        message: str, response: httpx.Response, *, body_type: object | None = None
    ) -> APIError:
        """Classify the HTTP failure and preserve its documented response body."""
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if body_type is None and content_type == "application/problem+json":
            from .types import Problem

            body_type = Problem
        try:
            body = response.json()
        except ValueError:
            body = response.text
        else:
            if body_type is not None:
                try:
                    body = pydantic.TypeAdapter(body_type).validate_python(body)
                except pydantic.ValidationError:
                    pass
        if 400 <= response.status_code < 600:
            error_type = _STATUS_ERRORS.get(response.status_code, APIStatusError)
            if response.status_code >= 500:
                error_type = InternalServerError
            return error_type(message, body=body, response=response)
        return APIError(message, status=response.status_code, body=body, response=response)


class APIStatusError(APIError):
    """The API returned an HTTP 4xx or 5xx response."""

    status: int
    response: httpx.Response

    def __init__(
        self, message: str, *, response: httpx.Response, body: object | None = None
    ) -> None:
        super().__init__(message, status=response.status_code, body=body, response=response)


class BadRequestError(APIStatusError):
    """The API rejected the request (HTTP 400)."""


class AuthenticationError(APIStatusError):
    """Authentication failed (HTTP 401)."""


class PermissionDeniedError(APIStatusError):
    """The credentials do not allow this operation (HTTP 403)."""


class NotFoundError(APIStatusError):
    """The requested resource was not found (HTTP 404)."""


class ConflictError(APIStatusError):
    """The request conflicts with the resource's current state (HTTP 409)."""


class UnprocessableEntityError(APIStatusError):
    """The API could not process the request (HTTP 422)."""


class RateLimitError(APIStatusError):
    """The API's request limit was exceeded (HTTP 429)."""


class InternalServerError(APIStatusError):
    """The API returned a server error (HTTP 5xx)."""


class APIConnectionError(APIError):
    """The request failed because of a connection or transport error."""

    def __init__(self, *, request: httpx.Request, message: str = "Connection error.") -> None:
        super().__init__(message)
        self.request = request


class APITimeoutError(APIConnectionError):
    """The request timed out."""

    def __init__(self, *, request: httpx.Request) -> None:
        super().__init__(request=request, message="Request timed out.")


_STATUS_ERRORS: dict[int, type[APIStatusError]] = {
    400: BadRequestError,
    401: AuthenticationError,
    403: PermissionDeniedError,
    404: NotFoundError,
    409: ConflictError,
    422: UnprocessableEntityError,
    429: RateLimitError,
}


@contextmanager
def _wrap_request_errors() -> Iterator[None]:
    try:
        yield
    except httpx.TimeoutException as cause:
        raise APITimeoutError(request=cause.request) from cause
    except httpx.RequestError as cause:
        raise APIConnectionError(request=cause.request) from cause

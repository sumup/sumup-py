import asyncio
import datetime

import httpx
import pytest

from sumup import APIError, errors
from sumup.checkouts import AsyncCheckoutsResource, CheckoutsResource
from sumup.payouts import ListPayoutsV1400Response
from sumup.readers import AsyncReadersResource, ReadersResource
from sumup.types import (
    CustomerValidationError,
    DetailsError,
    Error,
    ErrorExtended,
    ErrorForbidden,
    Problem,
    Unauthorized,
)


@pytest.mark.parametrize(
    "content,expected_body",
    [
        pytest.param(
            b'{"error_code":"INVALID_QUERY","extra":{"field":"amount"}}',
            {"error_code": "INVALID_QUERY", "extra": {"field": "amount"}},
            id="object",
        ),
        pytest.param(b'[{"error_code":"INVALID"}]', [{"error_code": "INVALID"}], id="array"),
        pytest.param(
            b'"{\\"error_code\\":\\"INVALID\\"}"', '{"error_code":"INVALID"}', id="string"
        ),
        pytest.param(b"0", 0, id="number"),
        pytest.param(b"false", False, id="boolean"),
        pytest.param(b"null", None, id="null"),
        pytest.param(b"Service unavailable", "Service unavailable", id="text"),
        pytest.param(b"<html>Bad gateway</html>", "<html>Bad gateway</html>", id="html"),
        pytest.param(b'{"error_code":', '{"error_code":', id="malformed-json"),
        pytest.param(b"", "", id="empty"),
    ],
)
def test_api_error_from_response(content, expected_body):
    response = httpx.Response(400, content=content, headers={"X-Request-ID": "request-123"})

    error = APIError.from_response("Request failed", response)

    assert str(error) == "HTTP 400: Request failed"
    assert error.message == "Request failed"
    assert error.status == 400
    assert error.body == expected_body
    assert error.response is response
    assert error.response.content == content
    assert error.response.headers["X-Request-ID"] == "request-123"


@pytest.mark.parametrize("body", ['{"error_code":"INVALID"}', {"error_code": "INVALID"}, None])
def test_api_error_constructor_preserves_body(body):
    error = APIError("Request failed", status=None, body=body)

    assert error.body is body
    assert error.status is None
    assert error.response is None


def test_api_error_from_response_uses_documented_type():
    response = httpx.Response(
        401,
        json={
            "type": "https://developer.sumup.com/problem/unauthorized",
            "title": "Unauthorized",
            "trace_id": "trace-123",
        },
    )

    error = APIError.from_response("Request failed", response, body_type=Problem)

    assert isinstance(error, errors.AuthenticationError)
    assert isinstance(error.body, Problem)
    assert error.problem is error.body
    assert error.body.title == "Unauthorized"
    assert error.body.additional_properties["trace_id"] == "trace-123"
    assert error.status == 401
    assert error.response is response


@pytest.mark.parametrize("body", [None, Error(message="Invalid request"), {"type": "about:blank"}])
def test_problem_property_returns_none_for_other_bodies(body):
    error = errors.BadRequestError("Request failed", response=httpx.Response(400), body=body)

    assert error.problem is None
    assert error.body is body


@pytest.mark.parametrize(
    "content,expected_body",
    [
        (b'{"detail":"Missing problem type"}', {"detail": "Missing problem type"}),
        (b"Service unavailable", "Service unavailable"),
    ],
)
def test_invalid_typed_body_preserves_api_error(content, expected_body):
    response = httpx.Response(401, content=content)

    error = APIError.from_response("Request failed", response, body_type=Problem)

    assert type(error) is errors.AuthenticationError
    assert error.body == expected_body
    assert error.status == 401
    assert error.response is response


@pytest.mark.parametrize(
    "content_type",
    ["application/problem+json", "Application/Problem+JSON; charset=utf-8"],
)
def test_api_error_recognizes_problem_content_type(content_type):
    response = httpx.Response(
        404,
        headers={"Content-Type": content_type},
        json={"type": "https://developer.sumup.com/problem/not-found", "detail": "Reader missing"},
    )

    error = APIError.from_response("Request failed", response)

    assert isinstance(error, errors.NotFoundError)
    assert isinstance(error.body, Problem)
    assert error.body.detail == "Reader missing"
    assert error.response is response


def test_problem_content_type_does_not_override_documented_type():
    response = httpx.Response(
        400,
        headers={"Content-Type": "application/problem+json"},
        json={"error_code": "INVALID", "message": "Invalid amount"},
    )

    error = APIError.from_response("Request failed", response, body_type=Error)

    assert isinstance(error.body, Error)
    assert error.body.message == "Invalid amount"


@pytest.mark.parametrize(
    "body,status,expected",
    [
        pytest.param(
            Problem(type="about:blank", title="Unauthorized", detail="Access token expired"),
            401,
            "HTTP 401: Access token expired",
            id="problem-detail",
        ),
        pytest.param(
            Problem(type="about:blank", title="Unauthorized"),
            401,
            "HTTP 401: Unauthorized",
            id="problem-title",
        ),
        pytest.param(Error(message="Invalid amount"), 400, "HTTP 400: Invalid amount", id="error"),
        pytest.param(
            DetailsError(title="Invalid currency", details="Currency XX is not supported"),
            400,
            "HTTP 400: Currency XX is not supported",
            id="details-error",
        ),
        pytest.param(
            ErrorForbidden(error_message="Missing scope"),
            403,
            "HTTP 403: Missing scope",
            id="error-message",
        ),
        pytest.param(
            [ErrorExtended(message="Invalid amount"), ErrorExtended(message="Invalid currency")],
            400,
            "HTTP 400: Invalid amount; Invalid currency",
            id="array",
        ),
        pytest.param(None, 502, "HTTP 502: Request failed", id="fallback"),
        pytest.param(None, None, "Request failed", id="no-response"),
    ],
)
def test_api_error_string_uses_server_message(body, status, expected):
    error = APIError("Request failed", status=status, body=body)

    assert str(error) == expected
    assert error.message == expected.removeprefix(f"HTTP {status}: ")


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    "status,content,expected_body,message,error_type",
    [
        pytest.param(
            404,
            b'{"error_code":"NOT_FOUND"}',
            Error(error_code="NOT_FOUND"),
            "The requested resource does not exist.",
            errors.NotFoundError,
            id="documented-error",
        ),
        pytest.param(
            401,
            b'{"type":"https://developer.sumup.com/problem/unauthorized","title":"Unauthorized"}',
            Problem(type="https://developer.sumup.com/problem/unauthorized", title="Unauthorized"),
            "Unauthorized",
            errors.AuthenticationError,
            id="problem",
        ),
        pytest.param(
            502,
            b"Bad gateway",
            "Bad gateway",
            "Unexpected response",
            errors.InternalServerError,
            id="unexpected-error",
        ),
    ],
)
def test_resource_api_errors(use_async, status, content, expected_body, message, error_type):
    response = httpx.Response(status, content=content, headers={"X-Request-ID": "request-123"})
    transport = httpx.MockTransport(lambda _: response)

    with pytest.raises(error_type) as raised:
        if use_async:

            async def run():
                async with httpx.AsyncClient(
                    base_url="https://api.sumup.test", transport=transport
                ) as client:
                    await AsyncCheckoutsResource(client).get("checkout-123")

            asyncio.run(run())
        else:
            with httpx.Client(base_url="https://api.sumup.test", transport=transport) as client:
                CheckoutsResource(client).get("checkout-123")

    error = raised.value
    assert error.status == status
    assert error.body == expected_body
    assert type(error) is error_type
    assert error.message == message
    assert error.args == (message,)
    assert error.response is response
    assert error.response.text == content.decode()
    assert error.response.headers["X-Request-ID"] == "request-123"


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("multiple", [False, True], ids=["object", "array"])
def test_inline_error_union(use_async, multiple):
    payload = {"error_code": "INVALID", "message": "Invalid card", "param": "card.number"}
    expected = ErrorExtended(**payload)
    response = httpx.Response(400, json=[payload] if multiple else payload)
    transport = httpx.MockTransport(lambda _: response)

    with pytest.raises(errors.BadRequestError) as raised:
        if use_async:

            async def run():
                async with httpx.AsyncClient(
                    base_url="https://api.sumup.test", transport=transport
                ) as client:
                    await AsyncCheckoutsResource(client).process(
                        "checkout-123", payment_type="card"
                    )

            asyncio.run(run())
        else:
            with httpx.Client(base_url="https://api.sumup.test", transport=transport) as client:
                CheckoutsResource(client).process("checkout-123", payment_type="card")

    assert raised.value.body == ([expected] if multiple else expected)
    assert raised.value.status == 400
    assert raised.value.response is response


def test_inline_error_object(sdk_factory):
    response = httpx.Response(
        400,
        json={
            "error_code": "INVALID",
            "error_message": "Invalid customer",
            "instance": "error-123",
        },
    )
    sdk = sdk_factory(lambda _: response)

    with pytest.raises(errors.BadRequestError) as raised:
        sdk.customers.create(customer_id="customer-123")

    assert isinstance(raised.value.body, CustomerValidationError)
    assert raised.value.body.error_message == "Invalid customer"
    assert raised.value.body.instance == "error-123"
    assert str(raised.value) == "HTTP 400: Invalid customer"


def test_error_array(sdk_factory):
    payload = {"error_code": "INVALID", "message": "Invalid date range", "param": "start_date"}
    sdk = sdk_factory(lambda _: httpx.Response(400, json=[payload]))

    with pytest.raises(errors.BadRequestError) as raised:
        sdk.payouts.list(
            "merchant-123",
            start_date=datetime.date(2026, 1, 2),
            end_date=datetime.date(2026, 1, 1),
        )

    expected: ListPayoutsV1400Response = [ErrorExtended(**payload)]
    assert raised.value.body == expected


def test_status_errors_share_the_api_error_base():
    response = httpx.Response(401, json={"type": "about:blank", "detail": "Access token expired"})

    with pytest.raises(APIError) as raised:
        raise APIError.from_response("Request failed", response, body_type=Problem)

    assert isinstance(raised.value, errors.APIStatusError)
    assert isinstance(raised.value, errors.AuthenticationError)
    assert isinstance(raised.value.body, Problem)
    assert raised.value.body.detail == "Access token expired"
    assert raised.value.response is response


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    "content_type,payload,body_type",
    [
        (
            "application/json; charset=utf-8",
            {"errors": {"detail": "Invalid credentials", "type": "INVALID_BEARER_TOKEN"}},
            Unauthorized,
        ),
        (
            "Application/Problem+JSON; charset=utf-8",
            {"type": "about:blank", "detail": "Invalid credentials"},
            Problem,
        ),
        (
            "application/xml",
            {"errors": {"detail": "Invalid credentials", "type": "INVALID_BEARER_TOKEN"}},
            dict,
        ),
    ],
)
def test_reader_error_formats(use_async, content_type, payload, body_type):
    response = httpx.Response(401, json=payload, headers={"Content-Type": content_type})
    transport = httpx.MockTransport(lambda _: response)

    with pytest.raises(APIError) as raised:
        if use_async:

            async def run():
                async with httpx.AsyncClient(
                    base_url="https://api.sumup.test", transport=transport
                ) as client:
                    await AsyncReadersResource(client).get_status("merchant-123", "reader-123")

            asyncio.run(run())
        else:
            with httpx.Client(base_url="https://api.sumup.test", transport=transport) as client:
                ReadersResource(client).get_status("merchant-123", "reader-123")

    error = raised.value
    assert type(error) is errors.AuthenticationError
    assert isinstance(error.body, body_type)
    assert error.status == 401
    assert error.response is response
    if body_type is not dict:
        assert error.message == "Invalid credentials"


@pytest.mark.parametrize(
    "status,error_type",
    [
        (400, errors.BadRequestError),
        (401, errors.AuthenticationError),
        (403, errors.PermissionDeniedError),
        (404, errors.NotFoundError),
        (409, errors.ConflictError),
        (422, errors.UnprocessableEntityError),
        (429, errors.RateLimitError),
        (500, errors.InternalServerError),
        (599, errors.InternalServerError),
        (418, errors.APIStatusError),
        (302, APIError),
        (202, APIError),
    ],
)
def test_http_error_categories_do_not_depend_on_body(status, error_type):
    response = httpx.Response(status, text="<html>Unexpected response</html>")

    error = APIError.from_response("Request failed", response)

    assert type(error) is error_type
    assert error.body == response.text
    assert error.response is response
    assert error.status == status


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    "cause_type,error_type",
    [
        (httpx.ConnectError, errors.APIConnectionError),
        (httpx.ReadTimeout, errors.APITimeoutError),
    ],
)
def test_resource_transport_errors(use_async, cause_type, error_type):
    requests = []

    def handler(request):
        requests.append(request)
        raise cause_type("Transport failed", request=request)

    transport = httpx.MockTransport(handler)
    with pytest.raises(APIError) as raised:
        if use_async:

            async def run():
                async with httpx.AsyncClient(
                    base_url="https://api.sumup.test", transport=transport
                ) as client:
                    await AsyncCheckoutsResource(client).get("checkout-123")

            asyncio.run(run())
        else:
            with httpx.Client(base_url="https://api.sumup.test", transport=transport) as client:
                CheckoutsResource(client).get("checkout-123")

    error = raised.value
    assert type(error) is error_type
    assert isinstance(error, errors.APIConnectionError)
    assert isinstance(error.__cause__, cause_type)
    assert error.request is requests[0]
    assert error.request is error.__cause__.request
    assert error.response is None
    assert error.status is None
    assert error.body is None
    assert isinstance(error.message, str)

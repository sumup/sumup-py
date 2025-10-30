from collections.abc import Callable

import httpx
import pytest

from sumup import Sumup
from sumup.transactions import ListTransactionsV21Params


@pytest.fixture
def sdk_factory():
    created_clients: list[httpx.Client] = []

    def factory(handler: Callable[[httpx.Request], httpx.Response]) -> Sumup:
        transport = httpx.MockTransport(handler)
        sdk = Sumup(api_key="test", base_url="https://api.sumup.test")
        original_client = sdk._client
        sdk._client = httpx.Client(
            base_url=original_client.base_url,
            timeout=original_client.timeout,
            headers=original_client.headers,
            transport=transport,
        )
        original_client.close()
        created_clients.append(sdk._client)
        return sdk

    yield factory

    for client in created_clients:
        client.close()


@pytest.mark.parametrize(
    ("params", "expected_query_items"),
    [
        (ListTransactionsV21Params(limit=10), [("limit", "10")]),
        (None, []),
        (
            ListTransactionsV21Params(statuses=["SUCCESSFUL", "FAILED"]),
            [("statuses", "SUCCESSFUL"), ("statuses", "FAILED")],
        ),
    ],
)
def test_transactions_list_query_params(params, expected_query_items, sdk_factory):
    captured_request: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["request"] = request
        return httpx.Response(200, json={"items": []})

    sdk = sdk_factory(handler)
    kwargs = {}
    if params is not None:
        kwargs["params"] = params

    response = sdk.transactions.list("merchant-123", **kwargs)

    assert response.items == []
    assert "request" in captured_request
    request = captured_request["request"]
    assert request.url.path == "/v2.1/merchants/merchant-123/transactions/history"
    assert list(request.url.params.multi_items()) == expected_query_items

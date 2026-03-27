import httpx
import pytest
import typing

from sumup.transactions import ListTransactionsV21Params


@pytest.mark.parametrize(
    ("params", "expected_query_items"),
    [
        (ListTransactionsV21Params(limit=10), [("limit", "10")]),
        (None, []),
        (
            ListTransactionsV21Params(statuses=["SUCCESSFUL", "FAILED"]),
            [("statuses[]", "SUCCESSFUL"), ("statuses[]", "FAILED")],
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


def test_transactions_list_query_param_enums_are_typed():
    order_annotation = ListTransactionsV21Params.model_fields["order"].annotation

    assert typing.get_origin(order_annotation) is typing.Union
    assert typing.get_args(order_annotation) == (
        typing.Literal["ascending", "descending"],
        str,
        type(None),
    )

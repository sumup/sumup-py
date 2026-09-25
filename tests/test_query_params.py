import asyncio
import typing

import httpx
import pytest

from sumup._service import NotGivenType
from sumup.memberships.resource import AsyncMembershipsResource, MembershipsResource


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    ("kwargs", "expected_query"),
    [
        ({}, b""),
        (
            {"resource_parent_id": "", "resource_parent_type": ""},
            b"resource.parent.id=&resource.parent.type=",
        ),
        (
            {"resource_parent_id": "merchant-123", "resource_parent_type": "merchant"},
            b"resource.parent.id=merchant-123&resource.parent.type=merchant",
        ),
    ],
    ids=["omitted", "empty", "parent"],
)
def test_memberships_parent_filter_query_params(use_async, kwargs, expected_query):
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"items": [], "total_count": 0})

    transport = httpx.MockTransport(handler)
    if use_async:

        async def run():
            async with httpx.AsyncClient(
                base_url="https://api.sumup.test", transport=transport
            ) as client:
                return await AsyncMembershipsResource(client).list(**kwargs)

        response = asyncio.run(run())
    else:
        with httpx.Client(base_url="https://api.sumup.test", transport=transport) as client:
            response = MembershipsResource(client).list(**kwargs)

    assert response.items == []
    assert len(requests) == 1
    assert requests[0].url.path == "/v0.1/memberships"
    assert requests[0].url.query == expected_query


@pytest.mark.parametrize("resource", [MembershipsResource, AsyncMembershipsResource])
def test_memberships_parent_filters_accept_strings_without_none(resource):
    annotations = typing.get_type_hints(resource.list)
    for name in ("resource_parent_id", "resource_parent_type"):
        args = typing.get_args(annotations[name])
        assert str in args
        assert NotGivenType in args
        assert type(None) not in args


@pytest.mark.parametrize(
    ("kwargs", "expected_query_items"),
    [
        ({"limit": 10}, [("limit", "10")]),
        ({}, []),
        (
            {"statuses": ["SUCCESSFUL", "FAILED"]},
            [("statuses[]", "SUCCESSFUL"), ("statuses[]", "FAILED")],
        ),
    ],
)
def test_transactions_list_query_params(kwargs, expected_query_items, sdk_factory):
    captured_request: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["request"] = request
        return httpx.Response(200, json={"items": []})

    sdk = sdk_factory(handler)
    response = sdk.transactions.list("merchant-123", **kwargs)

    assert response.items == []
    assert "request" in captured_request
    request = captured_request["request"]
    assert request.url.path == "/v2.1/merchants/merchant-123/transactions/history"
    assert list(request.url.params.multi_items()) == expected_query_items


def test_transactions_list_query_param_enums_are_typed():
    annotations = sdk_annotations()
    order_annotation = annotations["order"]

    assert typing.get_origin(order_annotation) is typing.Union
    assert typing.get_args(order_annotation) == (
        typing.Literal["ascending", "descending"],
        str,
        NotGivenType,
    )


def sdk_annotations():
    from sumup.transactions.resource import TransactionsResource

    return typing.get_type_hints(TransactionsResource.list)

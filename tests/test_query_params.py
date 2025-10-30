import httpx

from sumup import Sumup
from sumup.merchant import GetAccountParams


def test_query_params_serialized_with_aliases():
    captured_request: dict[str, httpx.QueryParams] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["params"] = request.url.params
        return httpx.Response(200, json={})

    transport = httpx.MockTransport(handler)

    with httpx.Client(base_url="https://api.sumup.test", transport=transport) as mock_client:
        sdk = Sumup(client=mock_client)
        params = GetAccountParams(include=["merchant_profile", "permissions"])
        serialized = params.model_dump(by_alias=True, exclude_none=True)
        assert serialized == {"include[]": ["merchant_profile", "permissions"]}

        response = sdk.merchant.get(params=params)

    assert response is not None
    assert "params" in captured_request
    query_params = captured_request["params"]
    items = list(query_params.multi_items())
    assert items == [
        ("include[]", "merchant_profile"),
        ("include[]", "permissions"),
    ]

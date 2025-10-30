import httpx
import sys
from pathlib import Path
import importlib

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

for module in list(sys.modules):
    if module == "sumup" or module.startswith("sumup."):
        sys.modules.pop(module, None)

Sumup = importlib.import_module("sumup").Sumup
GetAccountParams = importlib.import_module("sumup.merchant.resource").GetAccountParams


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

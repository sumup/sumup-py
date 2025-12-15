import json

import httpx

from sumup.readers import CreateReaderCheckoutBody, CreateReaderCheckoutBodyTotalAmount
from sumup.subaccounts import UpdateSubAccountBody


def test_create_reader_checkout_omits_null_fields(sdk_factory):
    captured_request: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["request"] = request
        return httpx.Response(201, json={"data": {"client_transaction_id": "txn-123"}})

    sdk = sdk_factory(handler)
    body = CreateReaderCheckoutBody(
        total_amount=CreateReaderCheckoutBodyTotalAmount(currency="EUR", minor_unit=2, value=1500)
    )

    response = sdk.readers.create_checkout("merchant-123", "reader-456", body)

    assert response.data.client_transaction_id == "txn-123"
    assert "request" in captured_request
    request = captured_request["request"]
    assert request.url.path == "/v0.1/merchants/merchant-123/readers/reader-456/checkout"
    assert json.loads(request.content) == {
        "total_amount": {"currency": "EUR", "minor_unit": 2, "value": 1500}
    }


def test_update_subaccount_accepts_explicit_null_fields(sdk_factory):
    captured_request: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["request"] = request
        return httpx.Response(
            200,
            json={
                "account_type": "operator",
                "created_at": "2024-01-01T00:00:00Z",
                "disabled": False,
                "id": 1,
                "permissions": {
                    "admin": False,
                    "create_moto_payments": False,
                    "create_referral": False,
                    "full_transaction_history_view": False,
                    "refund_transactions": False,
                },
                "updated_at": "2024-01-02T00:00:00Z",
                "username": "operator@example.com",
                "nickname": None,
            },
        )

    sdk = sdk_factory(handler)
    body = UpdateSubAccountBody(nickname=None)

    response = sdk.subaccounts.update_sub_account(1, body)

    assert response.nickname is None
    assert "request" in captured_request
    request = captured_request["request"]
    assert request.url.path == "/v0.1/me/accounts/1"
    assert json.loads(request.content) == {"nickname": None}

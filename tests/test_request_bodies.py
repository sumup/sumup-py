import datetime
import json
import httpx


def test_create_reader_checkout_omits_null_fields(sdk_factory):
    captured_request: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["request"] = request
        return httpx.Response(201, json={"data": {"client_transaction_id": "txn-123"}})

    sdk = sdk_factory(handler)
    response = sdk.readers.create_checkout(
        "merchant-123",
        "reader-456",
        total_amount={"currency": "EUR", "minor_unit": 2, "value": 1500},
    )

    assert response.data.client_transaction_id == "txn-123"
    assert "request" in captured_request
    request = captured_request["request"]
    assert request.url.path == "/v0.1/merchants/merchant-123/readers/reader-456/checkout"
    assert json.loads(request.content) == {
        "total_amount": {"currency": "EUR", "minor_unit": 2, "value": 1500}
    }


def test_create_checkout_serializes_datetime_fields(sdk_factory):
    captured_request: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["request"] = request
        return httpx.Response(201, json={"id": "checkout-123"})

    sdk = sdk_factory(handler)
    response = sdk.checkouts.create(
        amount=15.0,
        checkout_reference="checkout-ref",
        currency="EUR",
        merchant_code="merchant-123",
        valid_until=datetime.datetime(2024, 1, 2, 3, 4, 5),
    )

    assert response.id == "checkout-123"
    assert "request" in captured_request
    request = captured_request["request"]
    assert json.loads(request.content) == {
        "amount": 15.0,
        "checkout_reference": "checkout-ref",
        "currency": "EUR",
        "merchant_code": "merchant-123",
        "valid_until": "2024-01-02T03:04:05",
    }

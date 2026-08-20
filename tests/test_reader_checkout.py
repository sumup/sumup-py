import datetime

import httpx


def test_get_reader_checkout_accepts_pending_null_fields(sdk_factory):
    captured_request: dict[str, httpx.Request] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request["request"] = request
        return httpx.Response(
            200,
            json={
                "data": {
                    "card_type": None,
                    "checkout_id": "00e33a36-c99b-4cb2-b635-b90c1455c9c8",
                    "client_transaction_id": "00e33a36-c99b-4cb2-b635-b90c1455c9c8",
                    "created_at": "2026-07-07T20:41:16.315434Z",
                    "installments": None,
                    "payment_status": None,
                    "payment_type": "card",
                    "reader_firmware_version": "3.3.3.21",
                    "reader_serial_number": "1234567890",
                    "status": "pending",
                    "total_amount": {"currency": "EUR", "minor_unit": 2, "value": 1000},
                    "updated_at": "2026-07-07T20:42:18.117244Z",
                    "valid_until": None,
                }
            },
        )

    sdk = sdk_factory(handler)
    checkout = sdk.readers.get_checkout(
        "merchant-123",
        "reader-456",
        "00e33a36-c99b-4cb2-b635-b90c1455c9c8",
    )

    assert "request" in captured_request
    assert checkout.data.status == "pending"
    assert checkout.data.card_type is None
    assert checkout.data.installments is None
    assert checkout.data.payment_status is None
    assert checkout.data.valid_until is None
    assert checkout.data.total_amount.value == 1000
    assert checkout.data.created_at == datetime.datetime(
        2026, 7, 7, 20, 41, 16, 315434, tzinfo=datetime.timezone.utc
    )

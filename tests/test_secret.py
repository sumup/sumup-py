from sumup._secret import Secret
from sumup._service import serialize_request_data


def test_secret_masks_repr_but_preserves_value() -> None:
    secret = Secret("super-secret")

    assert secret.value() == "super-secret"
    assert str(secret) == "***"
    assert repr(secret) == "Secret('***')"
    assert secret == "super-secret"


def test_request_serialization_dumps_secret_plain_text() -> None:
    payload = {
        "email": "user@example.com",
        "password": Secret("super-secret"),
        "nested": {"password": Secret("super-secret")},
    }

    dumped = serialize_request_data(payload)

    assert dumped == {
        "email": "user@example.com",
        "password": "super-secret",
        "nested": {"password": "super-secret"},
    }

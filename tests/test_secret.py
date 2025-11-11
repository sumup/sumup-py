from sumup._secret import Secret
from sumup.members.resource import CreateMerchantMemberBody


def test_secret_masks_repr_but_preserves_value() -> None:
    secret = Secret("super-secret")

    assert secret.value() == "super-secret"
    assert str(secret) == "***"
    assert repr(secret) == "Secret('***')"
    assert secret == "super-secret"


def test_password_fields_use_secret_and_dump_plain_text() -> None:
    body = CreateMerchantMemberBody(
        email="user@example.com",
        roles=["role_manager"],
        is_managed_user=True,
        password=Secret("super-secret"),
    )

    assert isinstance(body.password, Secret)
    dumped = body.model_dump()
    assert dumped["password"] == "super-secret"

    body_repr = repr(body)
    assert "super-secret" not in body_repr

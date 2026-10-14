import pytest
from pydantic import ValidationError

from sumup.types import Address


def test_address_country_retains_its_string_type():
    address = Address(country="DE")
    assert address.country == "DE"
    assert address.model_dump(exclude_none=True) == {"country": "DE"}


def test_address_country_rejects_an_object():
    with pytest.raises(ValidationError):
        Address.model_validate({"country": {}})

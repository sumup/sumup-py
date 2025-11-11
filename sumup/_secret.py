from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

_MASK = "***"


@dataclass(frozen=True)
class Secret:
    """
    Secret wraps sensitive string values (e.g. passwords) so they stay masked in
    repr/log output while still serializing as plain strings in API requests.
    """

    _value: str

    def __post_init__(self) -> None:
        if not isinstance(self._value, str):
            raise TypeError("Secret value must be a string")

    def value(self) -> str:
        """Return the underlying secret value."""
        return self._value

    def __str__(self) -> str:
        return _MASK

    def __repr__(self) -> str:
        return f"Secret({_MASK!r})"

    def __bool__(self) -> bool:
        return bool(self._value)

    def __hash__(self) -> int:
        return hash(self._value)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Secret):
            return self._value == other._value
        if isinstance(other, str):
            return self._value == other
        return NotImplemented

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        """Allow pydantic models to accept raw strings but serialize as plain str."""

        def validate(value: Any) -> "Secret":
            if isinstance(value, Secret):
                return value
            if isinstance(value, str):
                return cls(value)
            raise TypeError("Secret value must be a string")

        def serialize(value: "Secret") -> str:
            return value._value

        return core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.plain_serializer_function_ser_schema(
                serialize, when_used="always"
            ),
        )

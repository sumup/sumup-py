# Code generated by `py-sdk-gen`. DO NOT EDIT.
from datetime import date
import typing
import pydantic

type FinancialPayoutStatus = typing.Literal["FAILED", "SUCCESSFUL"]

type FinancialPayoutType = typing.Literal[
    "BALANCE_DEDUCTION",
    "CHARGE_BACK_DEDUCTION",
    "DD_RETURN_DEDUCTION",
    "PAYOUT",
    "REFUND_DEDUCTION",
]


class FinancialPayout(pydantic.BaseModel):
    """
    FinancialPayout is a schema definition.
    """

    amount: typing.Optional[float] = None

    currency: typing.Optional[str] = None

    date: typing.Optional[date] = None
    """
	Format: date
	"""

    fee: typing.Optional[float] = None

    id: typing.Optional[int] = None

    reference: typing.Optional[str] = None

    status: typing.Optional[FinancialPayoutStatus] = None

    transaction_code: typing.Optional[str] = None

    type: typing.Optional[FinancialPayoutType] = None


type FinancialPayouts = list[FinancialPayout]
"""
FinancialPayouts is a schema definition.
"""


class Error(pydantic.BaseModel):
    """
    Error message structure.
    """

    error_code: typing.Optional[str] = None
    """
	Platform code for the error.
	"""

    message: typing.Optional[str] = None
    """
	Short description of the error.
	"""

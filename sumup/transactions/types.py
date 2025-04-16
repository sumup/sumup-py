# Code generated by `py-sdk-gen`. DO NOT EDIT.
from datetime import datetime, date
import typing
import pydantic


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


type Currency = typing.Literal[
    "BGN",
    "BRL",
    "CHF",
    "CLP",
    "CZK",
    "DKK",
    "EUR",
    "GBP",
    "HRK",
    "HUF",
    "NOK",
    "PLN",
    "RON",
    "SEK",
    "USD",
]

type TransactionMixinBaseStatus = typing.Literal["CANCELLED", "FAILED", "PENDING", "SUCCESSFUL"]

type TransactionMixinBasePaymentType = typing.Literal["BOLETO", "ECOM", "RECURRING"]


class TransactionMixinBase(pydantic.BaseModel):
    """
    Details of the transaction.
    """

    amount: typing.Optional[float] = None
    """
	Total amount of the transaction.
	"""

    currency: typing.Optional[Currency] = None
    """
	Three-letter [ISO4217](https://en.wikipedia.org/wiki/ISO_4217) code of the currency for the amount. Currently supportedcurrency values are enumerated above.
	"""

    id: typing.Optional[str] = None
    """
	Unique ID of the transaction.
	"""

    installments_count: typing.Optional[int] = None
    """
	Current number of the installment for deferred payments.
	Min: 1
	"""

    payment_type: typing.Optional[TransactionMixinBasePaymentType] = None
    """
	Payment type used for the transaction.
	"""

    status: typing.Optional[TransactionMixinBaseStatus] = None
    """
	Current status of the transaction.
	"""

    timestamp: typing.Optional[datetime] = None
    """
	Date and time of the creation of the transaction. Response format expressed according to [ISO8601](https://en.wikipedia.org/wiki/ISO_8601) code.
	"""

    transaction_code: typing.Optional[str] = None
    """
	Transaction code returned by the acquirer/processing entity after processing the transaction.
	"""


type TransactionMixinCheckoutEntryMode = typing.Literal["BOLETO", "CUSTOMER_ENTRY"]


class TransactionMixinCheckout(pydantic.BaseModel):
    """
    TransactionMixinCheckout is a schema definition.
    """

    auth_code: typing.Optional[str] = None
    """
	Authorization code for the transaction sent by the payment card issuer or bank. Applicable only to card payments.
	"""

    entry_mode: typing.Optional[TransactionMixinCheckoutEntryMode] = None
    """
	Entry mode of the payment details.
	"""

    internal_id: typing.Optional[int] = None
    """
	Internal unique ID of the transaction on the SumUp platform.
	"""

    merchant_code: typing.Optional[str] = None
    """
	Unique code of the registered merchant to whom the payment is made.
	"""

    tip_amount: typing.Optional[float] = None
    """
	Amount of the tip (out of the total transaction amount).
	"""

    vat_amount: typing.Optional[float] = None
    """
	Amount of the applicable VAT (out of the total transaction amount).
	"""


type TransactionMixinHistoryPayoutPlan = typing.Literal[
    "ACCELERATED_INSTALLMENT", "SINGLE_PAYMENT", "TRUE_INSTALLMENT"
]


class TransactionMixinHistory(pydantic.BaseModel):
    """
    TransactionMixinHistory is a schema definition.
    """

    payout_plan: typing.Optional[TransactionMixinHistoryPayoutPlan] = None
    """
	Payout plan of the registered user at the time when the transaction was made.
	"""

    payouts_received: typing.Optional[int] = None
    """
	Number of payouts that are made to the registered user specified in the `user` property.
	"""

    payouts_total: typing.Optional[int] = None
    """
	Total number of payouts to the registered user specified in the `user` property.
	"""

    product_summary: typing.Optional[str] = None
    """
	Short description of the payment. The value is taken from the `description` property of the related checkout resource.
	"""


type Lat = float
"""
Latitude value from the coordinates of the payment location (as received from the payment terminal reader).
Min: 0
Max: 90
"""

type Lon = float
"""
Longitude value from the coordinates of the payment location (as received from the payment terminal reader).
Min: 0
Max: 180
"""

type HorizontalAccuracy = float
"""
Indication of the precision of the geographical position received from the payment terminal.
"""

type CardResponseType = typing.Literal[
    "AMEX",
    "CUP",
    "DINERS",
    "DISCOVER",
    "ELO",
    "ELV",
    "HIPERCARD",
    "JCB",
    "MAESTRO",
    "MASTERCARD",
    "UNKNOWN",
    "VISA",
    "VISA_ELECTRON",
    "VISA_VPAY",
]


class CardResponse(pydantic.BaseModel):
    """
    Details of the payment card.
    """

    last_4_digits: typing.Optional[str] = None
    """
	Last 4 digits of the payment card number.
	Read only
	Min length: 4
	Max length: 4
	"""

    type: typing.Optional[CardResponseType] = None
    """
	Issuing card network of the payment card.
	Read only
	"""


class Product(pydantic.BaseModel):
    """
    Details of the product for which the payment is made.
    """

    name: typing.Optional[str] = None
    """
	Name of the product from the merchant's catalog.
	"""

    price: typing.Optional[float] = None
    """
	Price of the product without VAT.
	"""

    price_with_vat: typing.Optional[float] = None
    """
	Price of a single product item with VAT.
	"""

    quantity: typing.Optional[float] = None
    """
	Number of product items for the purchase.
	"""

    single_vat_amount: typing.Optional[float] = None
    """
	Amount of the VAT for a single product item (calculated as the product of `price` and `vat_rate`, i.e. `single_vat_amount= price * vat_rate`).
	"""

    total_price: typing.Optional[float] = None
    """
	Total price of the product items without VAT (calculated as the product of `price` and `quantity`, i.e. `total_price= price * quantity`).
	"""

    total_with_vat: typing.Optional[float] = None
    """
	Total price of the product items including VAT (calculated as the product of `price_with_vat` and `quantity`, i.e.`total_with_vat = price_with_vat * quantity`).
	"""

    vat_amount: typing.Optional[float] = None
    """
	Total VAT amount for the purchase (calculated as the product of `single_vat_amount` and `quantity`, i.e. `vat_amount= single_vat_amount * quantity`).
	"""

    vat_rate: typing.Optional[float] = None
    """
	VAT rate applicable to the product.
	"""


type EventId = int
"""
Unique ID of the transaction event.
Format: int64
"""

type EventType = typing.Literal["CHARGE_BACK", "PAYOUT", "PAYOUT_DEDUCTION", "REFUND"]

type EventStatus = typing.Literal[
    "FAILED", "PAID_OUT", "PENDING", "REFUNDED", "SCHEDULED", "SUCCESSFUL"
]

type AmountEvent = float
"""
Amount of the event.
"""

type TimestampEvent = str
"""
Date and time of the transaction event.
"""


class TransactionEvent(pydantic.BaseModel):
    """
    Details of a transaction event.
    """

    amount: typing.Optional[AmountEvent] = None
    """
	Amount of the event.
	"""

    date: typing.Optional[date] = None
    """
	Date when the transaction event occurred.
	Format: date
	"""

    due_date: typing.Optional[date] = None
    """
	Date when the transaction event is due to occur.
	Format: date
	"""

    event_type: typing.Optional[EventType] = None
    """
	Type of the transaction event.
	"""

    id: typing.Optional[EventId] = None
    """
	Unique ID of the transaction event.
	Format: int64
	"""

    installment_number: typing.Optional[int] = None
    """
	Consecutive number of the installment that is paid. Applicable only payout events, i.e. `event_type = PAYOUT`.
	"""

    status: typing.Optional[EventStatus] = None
    """
	Status of the transaction event.
	"""

    timestamp: typing.Optional[TimestampEvent] = None
    """
	Date and time of the transaction event.
	"""


class Link(pydantic.BaseModel):
    """
    Details of a link to a related resource.
    """

    href: typing.Optional[str] = None
    """
	URL for accessing the related resource.
	Format: uri
	"""

    rel: typing.Optional[str] = None
    """
	Specifies the relation to the current resource.
	"""

    type: typing.Optional[str] = None
    """
	Specifies the media type of the related resource.
	"""


class LinkRefund(pydantic.BaseModel):
    """
    LinkRefund is a schema definition.
    """

    href: typing.Optional[str] = None
    """
	URL for accessing the related resource.
	Format: uri
	"""

    max_amount: typing.Optional[float] = None
    """
	Maximum allowed amount for the refund.
	"""

    min_amount: typing.Optional[float] = None
    """
	Minimum allowed amount for the refund.
	"""

    rel: typing.Optional[str] = None
    """
	Specifies the relation to the current resource.
	"""

    type: typing.Optional[str] = None
    """
	Specifies the media type of the related resource.
	"""


type TransactionId = str
"""
Unique ID of the transaction.
"""


class Event(pydantic.BaseModel):
    """
    Event is a schema definition.
    """

    amount: typing.Optional[AmountEvent] = None
    """
	Amount of the event.
	"""

    deducted_amount: typing.Optional[float] = None
    """
	Amount deducted for the event.
	"""

    deducted_fee_amount: typing.Optional[float] = None
    """
	Amount of the fee deducted for the event.
	"""

    fee_amount: typing.Optional[float] = None
    """
	Amount of the fee related to the event.
	"""

    id: typing.Optional[EventId] = None
    """
	Unique ID of the transaction event.
	Format: int64
	"""

    installment_number: typing.Optional[int] = None
    """
	Consecutive number of the installment.
	"""

    status: typing.Optional[EventStatus] = None
    """
	Status of the transaction event.
	"""

    timestamp: typing.Optional[TimestampEvent] = None
    """
	Date and time of the transaction event.
	"""

    transaction_id: typing.Optional[TransactionId] = None
    """
	Unique ID of the transaction.
	"""

    type: typing.Optional[EventType] = None
    """
	Type of the transaction event.
	"""


type TransactionFullStatus = typing.Literal["CANCELLED", "FAILED", "PENDING", "SUCCESSFUL"]

type TransactionFullPaymentType = typing.Literal["BOLETO", "ECOM", "RECURRING"]

type TransactionFullEntryMode = typing.Literal["BOLETO", "CUSTOMER_ENTRY"]

type TransactionFullPayoutPlan = typing.Literal[
    "ACCELERATED_INSTALLMENT", "SINGLE_PAYMENT", "TRUE_INSTALLMENT"
]

type TransactionFullSimplePaymentType = typing.Literal[
    "CASH", "CC_CUSTOMER_ENTERED", "CC_SIGNATURE", "ELV", "EMV", "MANUAL_ENTRY", "MOTO"
]

type TransactionFullVerificationMethod = typing.Literal[
    "confirmation code verified",
    "none",
    "offline pin",
    "offline pin + signature",
    "online pin",
    "signature",
]

type TransactionFullPayoutType = typing.Literal["BALANCE", "BANK_ACCOUNT", "PREPAID_CARD"]

type TransactionFullSimpleStatus = typing.Literal[
    "CANCELLED",
    "CANCEL_FAILED",
    "CHARGEBACK",
    "FAILED",
    "NON_COLLECTION",
    "PAID_OUT",
    "REFUNDED",
    "REFUND_FAILED",
    "SUCCESSFUL",
]


class TransactionFullLocation(pydantic.BaseModel):
    """
    Details of the payment location as received from the payment terminal.
    """

    horizontal_accuracy: typing.Optional[HorizontalAccuracy] = None
    """
	Indication of the precision of the geographical position received from the payment terminal.
	"""

    lat: typing.Optional[Lat] = None
    """
	Latitude value from the coordinates of the payment location (as received from the payment terminal reader).
	Min: 0
	Max: 90
	"""

    lon: typing.Optional[Lon] = None
    """
	Longitude value from the coordinates of the payment location (as received from the payment terminal reader).
	Min: 0
	Max: 180
	"""


class TransactionFull(pydantic.BaseModel):
    """
    TransactionFull is a schema definition.
    """

    amount: typing.Optional[float] = None
    """
	Total amount of the transaction.
	"""

    auth_code: typing.Optional[str] = None
    """
	Authorization code for the transaction sent by the payment card issuer or bank. Applicable only to card payments.
	"""

    card: typing.Optional[CardResponse] = None
    """
	Details of the payment card.
	"""

    currency: typing.Optional[Currency] = None
    """
	Three-letter [ISO4217](https://en.wikipedia.org/wiki/ISO_4217) code of the currency for the amount. Currently supportedcurrency values are enumerated above.
	"""

    entry_mode: typing.Optional[TransactionFullEntryMode] = None
    """
	Entry mode of the payment details.
	"""

    events: typing.Optional[list[Event]] = None
    """
	List of events related to the transaction.
	Unique items only
	"""

    horizontal_accuracy: typing.Optional[HorizontalAccuracy] = None
    """
	Indication of the precision of the geographical position received from the payment terminal.
	"""

    id: typing.Optional[str] = None
    """
	Unique ID of the transaction.
	"""

    installments_count: typing.Optional[int] = None
    """
	Current number of the installment for deferred payments.
	Min: 1
	"""

    internal_id: typing.Optional[int] = None
    """
	Internal unique ID of the transaction on the SumUp platform.
	"""

    lat: typing.Optional[Lat] = None
    """
	Latitude value from the coordinates of the payment location (as received from the payment terminal reader).
	Min: 0
	Max: 90
	"""

    links: typing.Optional[list[typing.Any]] = None
    """
	List of hyperlinks for accessing related resources.
	Unique items only
	"""

    local_time: typing.Optional[datetime] = None
    """
	Local date and time of the creation of the transaction.
	"""

    location: typing.Optional[TransactionFullLocation] = None
    """
	Details of the payment location as received from the payment terminal.
	"""

    lon: typing.Optional[Lon] = None
    """
	Longitude value from the coordinates of the payment location (as received from the payment terminal reader).
	Min: 0
	Max: 180
	"""

    merchant_code: typing.Optional[str] = None
    """
	Unique code of the registered merchant to whom the payment is made.
	"""

    payment_type: typing.Optional[TransactionFullPaymentType] = None
    """
	Payment type used for the transaction.
	"""

    payout_plan: typing.Optional[TransactionFullPayoutPlan] = None
    """
	Payout plan of the registered user at the time when the transaction was made.
	"""

    payout_type: typing.Optional[TransactionFullPayoutType] = None
    """
	Payout type for the transaction.
	"""

    payouts_received: typing.Optional[int] = None
    """
	Number of payouts that are made to the registered user specified in the `user` property.
	"""

    payouts_total: typing.Optional[int] = None
    """
	Total number of payouts to the registered user specified in the `user` property.
	"""

    product_summary: typing.Optional[str] = None
    """
	Short description of the payment. The value is taken from the `description` property of the related checkout resource.
	"""

    products: typing.Optional[list[Product]] = None
    """
	List of products from the merchant's catalogue for which the transaction serves as a payment.
	"""

    simple_payment_type: typing.Optional[TransactionFullSimplePaymentType] = None
    """
	Simple name of the payment type.
	"""

    simple_status: typing.Optional[TransactionFullSimpleStatus] = None
    """
	Status generated from the processing status and the latest transaction state.
	"""

    status: typing.Optional[TransactionFullStatus] = None
    """
	Current status of the transaction.
	"""

    tax_enabled: typing.Optional[bool] = None
    """
	Indicates whether tax deduction is enabled for the transaction.
	"""

    timestamp: typing.Optional[datetime] = None
    """
	Date and time of the creation of the transaction. Response format expressed according to [ISO8601](https://en.wikipedia.org/wiki/ISO_8601) code.
	"""

    tip_amount: typing.Optional[float] = None
    """
	Amount of the tip (out of the total transaction amount).
	"""

    transaction_code: typing.Optional[str] = None
    """
	Transaction code returned by the acquirer/processing entity after processing the transaction.
	"""

    transaction_events: typing.Optional[list[TransactionEvent]] = None
    """
	List of transaction events related to the transaction.
	"""

    username: typing.Optional[str] = None
    """
	Email address of the registered user (merchant) to whom the payment is made.
	Format: email
	"""

    vat_amount: typing.Optional[float] = None
    """
	Amount of the applicable VAT (out of the total transaction amount).
	"""

    vat_rates: typing.Optional[list[typing.Any]] = None
    """
	List of VAT rates applicable to the transaction.
	"""

    verification_method: typing.Optional[TransactionFullVerificationMethod] = None
    """
	Verification method used for the transaction.
	"""


type TransactionHistoryStatus = typing.Literal["CANCELLED", "FAILED", "PENDING", "SUCCESSFUL"]

type TransactionHistoryPaymentType = typing.Literal["BOLETO", "ECOM", "RECURRING"]

type TransactionHistoryPayoutPlan = typing.Literal[
    "ACCELERATED_INSTALLMENT", "SINGLE_PAYMENT", "TRUE_INSTALLMENT"
]

type TransactionHistoryType = typing.Literal["CHARGE_BACK", "PAYMENT", "REFUND"]

type TransactionHistoryCardType = typing.Literal[
    "AMEX",
    "CUP",
    "DINERS",
    "DISCOVER",
    "ELO",
    "ELV",
    "HIPERCARD",
    "JCB",
    "MAESTRO",
    "MASTERCARD",
    "UNKNOWN",
    "VISA",
    "VISA_ELECTRON",
    "VISA_VPAY",
]


class TransactionHistory(pydantic.BaseModel):
    """
    TransactionHistory is a schema definition.
    """

    amount: typing.Optional[float] = None
    """
	Total amount of the transaction.
	"""

    card_type: typing.Optional[TransactionHistoryCardType] = None
    """
	Issuing card network of the payment card used for the transaction.
	"""

    client_transaction_id: typing.Optional[str] = None
    """
	Client-specific ID of the transaction.
	"""

    currency: typing.Optional[Currency] = None
    """
	Three-letter [ISO4217](https://en.wikipedia.org/wiki/ISO_4217) code of the currency for the amount. Currently supportedcurrency values are enumerated above.
	"""

    id: typing.Optional[str] = None
    """
	Unique ID of the transaction.
	"""

    installments_count: typing.Optional[int] = None
    """
	Current number of the installment for deferred payments.
	Min: 1
	"""

    payment_type: typing.Optional[TransactionHistoryPaymentType] = None
    """
	Payment type used for the transaction.
	"""

    payout_plan: typing.Optional[TransactionHistoryPayoutPlan] = None
    """
	Payout plan of the registered user at the time when the transaction was made.
	"""

    payouts_received: typing.Optional[int] = None
    """
	Number of payouts that are made to the registered user specified in the `user` property.
	"""

    payouts_total: typing.Optional[int] = None
    """
	Total number of payouts to the registered user specified in the `user` property.
	"""

    product_summary: typing.Optional[str] = None
    """
	Short description of the payment. The value is taken from the `description` property of the related checkout resource.
	"""

    status: typing.Optional[TransactionHistoryStatus] = None
    """
	Current status of the transaction.
	"""

    timestamp: typing.Optional[datetime] = None
    """
	Date and time of the creation of the transaction. Response format expressed according to [ISO8601](https://en.wikipedia.org/wiki/ISO_8601) code.
	"""

    transaction_code: typing.Optional[str] = None
    """
	Transaction code returned by the acquirer/processing entity after processing the transaction.
	"""

    transaction_id: typing.Optional[TransactionId] = None
    """
	Unique ID of the transaction.
	"""

    type: typing.Optional[TransactionHistoryType] = None
    """
	Type of the transaction for the registered user specified in the `user` property.
	"""

    user: typing.Optional[str] = None
    """
	Email address of the registered user (merchant) to whom the payment is made.
	Format: email
	"""

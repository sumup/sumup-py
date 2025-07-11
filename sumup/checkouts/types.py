# Code generated by `py-sdk-gen`. DO NOT EDIT.
from datetime import datetime, date
import typing
import pydantic


class DetailsErrorFailedConstraint(pydantic.BaseModel):
    """
    DetailsErrorFailedConstraint is a schema definition.
    """

    message: typing.Optional[str] = None

    reference: typing.Optional[str] = None


class DetailsError(pydantic.BaseModel):
    """
    Error message structure.
    """

    details: typing.Optional[str] = None
    """
	Details of the error.
	"""

    failed_constraints: typing.Optional[list[DetailsErrorFailedConstraint]] = None

    status: typing.Optional[float] = None
    """
	The status code.
	"""

    title: typing.Optional[str] = None
    """
	Short title of the error.
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


Currency = typing.Literal[
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


class MandateResponse(pydantic.BaseModel):
    """
    Created mandate
    """

    merchant_code: typing.Optional[str] = None
    """
	Merchant code which has the mandate
	"""

    status: typing.Optional[str] = None
    """
	Mandate status
	"""

    type: typing.Optional[str] = None
    """
	Indicates the mandate type
	"""


TransactionMixinBaseStatus = typing.Literal["CANCELLED", "FAILED", "PENDING", "SUCCESSFUL"]

TransactionMixinBasePaymentType = typing.Literal["BOLETO", "ECOM", "RECURRING"]


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


TransactionMixinCheckoutEntryMode = typing.Literal["BOLETO", "CUSTOMER_ENTRY"]


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


CheckoutStatus = typing.Literal["FAILED", "PAID", "PENDING"]

CheckoutTransactionStatus = typing.Literal["CANCELLED", "FAILED", "PENDING", "SUCCESSFUL"]

CheckoutTransactionPaymentType = typing.Literal["BOLETO", "ECOM", "RECURRING"]

CheckoutTransactionEntryMode = typing.Literal["BOLETO", "CUSTOMER_ENTRY"]


class CheckoutTransaction(pydantic.BaseModel):
    """
    CheckoutTransaction is a schema definition.
    """

    amount: typing.Optional[float] = None
    """
	Total amount of the transaction.
	"""

    auth_code: typing.Optional[str] = None
    """
	Authorization code for the transaction sent by the payment card issuer or bank. Applicable only to card payments.
	"""

    currency: typing.Optional[Currency] = None
    """
	Three-letter [ISO4217](https://en.wikipedia.org/wiki/ISO_4217) code of the currency for the amount. Currently supportedcurrency values are enumerated above.
	"""

    entry_mode: typing.Optional[CheckoutTransactionEntryMode] = None
    """
	Entry mode of the payment details.
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

    merchant_code: typing.Optional[str] = None
    """
	Unique code of the registered merchant to whom the payment is made.
	"""

    payment_type: typing.Optional[CheckoutTransactionPaymentType] = None
    """
	Payment type used for the transaction.
	"""

    status: typing.Optional[CheckoutTransactionStatus] = None
    """
	Current status of the transaction.
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

    vat_amount: typing.Optional[float] = None
    """
	Amount of the applicable VAT (out of the total transaction amount).
	"""


class Checkout(pydantic.BaseModel):
    """
    Details of the payment checkout.
    """

    amount: typing.Optional[float] = None
    """
	Amount of the payment.
	"""

    checkout_reference: typing.Optional[str] = None
    """
	Unique ID of the payment checkout specified by the client application when creating the checkout resource.
	Max length: 90
	"""

    currency: typing.Optional[Currency] = None
    """
	Three-letter [ISO4217](https://en.wikipedia.org/wiki/ISO_4217) code of the currency for the amount. Currently supportedcurrency values are enumerated above.
	"""

    customer_id: typing.Optional[str] = None
    """
	Unique identification of a customer. If specified, the checkout session and payment instrument are associated withthe referenced customer.
	"""

    date: typing.Optional[datetime] = None
    """
	Date and time of the creation of the payment checkout. Response format expressed according to [ISO8601](https://en.wikipedia.org/wiki/ISO_8601) code.
	"""

    description: typing.Optional[str] = None
    """
	Short description of the checkout visible in the SumUp dashboard. The description can contribute to reporting, allowingeasier identification of a checkout.
	"""

    id: typing.Optional[str] = None
    """
	Unique ID of the checkout resource.
	Read only
	"""

    mandate: typing.Optional[MandateResponse] = None
    """
	Created mandate
	"""

    merchant_code: typing.Optional[str] = None
    """
	Unique identifying code of the merchant profile.
	"""

    return_url: typing.Optional[str] = None
    """
	URL to which the SumUp platform sends the processing status of the payment checkout.
	Format: uri
	"""

    status: typing.Optional[CheckoutStatus] = None
    """
	Current status of the checkout.
	"""

    transactions: typing.Optional[list[CheckoutTransaction]] = None
    """
	List of transactions related to the payment.
	Unique items only
	"""

    valid_until: typing.Optional[datetime] = None
    """
	Date and time of the checkout expiration before which the client application needs to send a processing request.If no value is present, the checkout does not have an expiration time.
	"""


class ErrorExtended(pydantic.BaseModel):
    """
    ErrorExtended is a schema definition.
    """

    error_code: typing.Optional[str] = None
    """
	Platform code for the error.
	"""

    message: typing.Optional[str] = None
    """
	Short description of the error.
	"""

    param: typing.Optional[str] = None
    """
	Parameter name (with relative location) to which the error applies. Parameters from embedded resources aredisplayed using dot notation. For example, `card.name` refers to the `name` parameter embedded in the `card`object.
	"""


class ErrorForbidden(pydantic.BaseModel):
    """
    Error message for forbidden requests.
    """

    error_code: typing.Optional[str] = None
    """
	Platform code for the error.
	"""

    error_message: typing.Optional[str] = None
    """
	Short description of the error.
	"""

    status_code: typing.Optional[str] = None
    """
	HTTP status code for the error.
	"""


CheckoutCreateRequestPurpose = typing.Literal["CHECKOUT", "SETUP_RECURRING_PAYMENT"]

CheckoutCreateRequestStatus = typing.Literal["FAILED", "PAID", "PENDING"]

CheckoutCreateRequestTransactionStatus = typing.Literal[
    "CANCELLED", "FAILED", "PENDING", "SUCCESSFUL"
]

CheckoutCreateRequestTransactionPaymentType = typing.Literal["BOLETO", "ECOM", "RECURRING"]

CheckoutCreateRequestTransactionEntryMode = typing.Literal["BOLETO", "CUSTOMER_ENTRY"]


class CheckoutCreateRequestTransaction(pydantic.BaseModel):
    """
    CheckoutCreateRequestTransaction is a schema definition.
    """

    amount: typing.Optional[float] = None
    """
	Total amount of the transaction.
	"""

    auth_code: typing.Optional[str] = None
    """
	Authorization code for the transaction sent by the payment card issuer or bank. Applicable only to card payments.
	"""

    currency: typing.Optional[Currency] = None
    """
	Three-letter [ISO4217](https://en.wikipedia.org/wiki/ISO_4217) code of the currency for the amount. Currently supportedcurrency values are enumerated above.
	"""

    entry_mode: typing.Optional[CheckoutCreateRequestTransactionEntryMode] = None
    """
	Entry mode of the payment details.
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

    merchant_code: typing.Optional[str] = None
    """
	Unique code of the registered merchant to whom the payment is made.
	"""

    payment_type: typing.Optional[CheckoutCreateRequestTransactionPaymentType] = None
    """
	Payment type used for the transaction.
	"""

    status: typing.Optional[CheckoutCreateRequestTransactionStatus] = None
    """
	Current status of the transaction.
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

    vat_amount: typing.Optional[float] = None
    """
	Amount of the applicable VAT (out of the total transaction amount).
	"""


class CheckoutCreateRequest(pydantic.BaseModel):
    """
    Details of the payment checkout.
    """

    amount: float
    """
	Amount of the payment.
	"""

    checkout_reference: str
    """
	Unique ID of the payment checkout specified by the client application when creating the checkout resource.
	Max length: 90
	"""

    currency: Currency
    """
	Three-letter [ISO4217](https://en.wikipedia.org/wiki/ISO_4217) code of the currency for the amount. Currently supportedcurrency values are enumerated above.
	"""

    merchant_code: str
    """
	Unique identifying code of the merchant profile.
	"""

    customer_id: typing.Optional[str] = None
    """
	Unique identification of a customer. If specified, the checkout session and payment instrument are associated withthe referenced customer.
	"""

    date: typing.Optional[datetime] = None
    """
	Date and time of the creation of the payment checkout. Response format expressed according to [ISO8601](https://en.wikipedia.org/wiki/ISO_8601) code.
	Readonly
	"""

    description: typing.Optional[str] = None
    """
	Short description of the checkout visible in the SumUp dashboard. The description can contribute to reporting, allowingeasier identification of a checkout.
	"""

    id: typing.Optional[str] = None
    """
	Unique ID of the checkout resource.
	Read only
	"""

    purpose: typing.Optional[CheckoutCreateRequestPurpose] = None
    """
	Purpose of the checkout.
	Default: "CHECKOUT"
	"""

    redirect_url: typing.Optional[str] = None
    """
	__Required__ for [APMs](https://developer.sumup.com/online-payments/apm/introduction) and __recommended__ forcard payments. Refers to a url where the end user is redirected once the payment processing completes. Ifnot specified, the [Payment Widget](https://developer.sumup.com/online-payments/tools/card-widget) renders [3DSchallenge](https://developer.sumup.com/online-payments/features/3ds) within an iframe instead of performing afull-page redirect.
	"""

    return_url: typing.Optional[str] = None
    """
	URL to which the SumUp platform sends the processing status of the payment checkout.
	Format: uri
	"""

    status: typing.Optional[CheckoutCreateRequestStatus] = None
    """
	Current status of the checkout.
	Read only
	"""

    transactions: typing.Optional[list[CheckoutCreateRequestTransaction]] = None
    """
	List of transactions related to the payment.
	Read only
	Unique items only
	"""

    valid_until: typing.Optional[datetime] = None
    """
	Date and time of the checkout expiration before which the client application needs to send a processing request.If no value is present, the checkout does not have an expiration time.
	"""


CheckoutSuccessStatus = typing.Literal["FAILED", "PAID", "PENDING"]

CheckoutSuccessTransactionStatus = typing.Literal["CANCELLED", "FAILED", "PENDING", "SUCCESSFUL"]

CheckoutSuccessTransactionPaymentType = typing.Literal["BOLETO", "ECOM", "RECURRING"]

CheckoutSuccessTransactionEntryMode = typing.Literal["BOLETO", "CUSTOMER_ENTRY"]


class CheckoutSuccessTransaction(pydantic.BaseModel):
    """
    CheckoutSuccessTransaction is a schema definition.
    """

    amount: typing.Optional[float] = None
    """
	Total amount of the transaction.
	"""

    auth_code: typing.Optional[str] = None
    """
	Authorization code for the transaction sent by the payment card issuer or bank. Applicable only to card payments.
	"""

    currency: typing.Optional[Currency] = None
    """
	Three-letter [ISO4217](https://en.wikipedia.org/wiki/ISO_4217) code of the currency for the amount. Currently supportedcurrency values are enumerated above.
	"""

    entry_mode: typing.Optional[CheckoutSuccessTransactionEntryMode] = None
    """
	Entry mode of the payment details.
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

    merchant_code: typing.Optional[str] = None
    """
	Unique code of the registered merchant to whom the payment is made.
	"""

    payment_type: typing.Optional[CheckoutSuccessTransactionPaymentType] = None
    """
	Payment type used for the transaction.
	"""

    status: typing.Optional[CheckoutSuccessTransactionStatus] = None
    """
	Current status of the transaction.
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

    vat_amount: typing.Optional[float] = None
    """
	Amount of the applicable VAT (out of the total transaction amount).
	"""


class CheckoutSuccessPaymentInstrument(pydantic.BaseModel):
    """
    Object containing token information for the specified payment instrument
    """

    token: typing.Optional[str] = None
    """
	Token value
	"""


class CheckoutSuccess(pydantic.BaseModel):
    """
    CheckoutSuccess is a schema definition.
    """

    amount: typing.Optional[float] = None
    """
	Amount of the payment.
	"""

    checkout_reference: typing.Optional[str] = None
    """
	Unique ID of the payment checkout specified by the client application when creating the checkout resource.
	Max length: 90
	"""

    currency: typing.Optional[Currency] = None
    """
	Three-letter [ISO4217](https://en.wikipedia.org/wiki/ISO_4217) code of the currency for the amount. Currently supportedcurrency values are enumerated above.
	"""

    customer_id: typing.Optional[str] = None
    """
	Unique identification of a customer. If specified, the checkout session and payment instrument are associated withthe referenced customer.
	"""

    date: typing.Optional[datetime] = None
    """
	Date and time of the creation of the payment checkout. Response format expressed according to [ISO8601](https://en.wikipedia.org/wiki/ISO_8601) code.
	"""

    description: typing.Optional[str] = None
    """
	Short description of the checkout visible in the SumUp dashboard. The description can contribute to reporting, allowingeasier identification of a checkout.
	"""

    id: typing.Optional[str] = None
    """
	Unique ID of the checkout resource.
	Read only
	"""

    mandate: typing.Optional[MandateResponse] = None
    """
	Created mandate
	"""

    merchant_code: typing.Optional[str] = None
    """
	Unique identifying code of the merchant profile.
	"""

    merchant_name: typing.Optional[str] = None
    """
	Name of the merchant
	"""

    payment_instrument: typing.Optional[CheckoutSuccessPaymentInstrument] = None
    """
	Object containing token information for the specified payment instrument
	"""

    redirect_url: typing.Optional[str] = None
    """
	Refers to a url where the end user is redirected once the payment processing completes.
	"""

    return_url: typing.Optional[str] = None
    """
	URL to which the SumUp platform sends the processing status of the payment checkout.
	Format: uri
	"""

    status: typing.Optional[CheckoutSuccessStatus] = None
    """
	Current status of the checkout.
	"""

    transaction_code: typing.Optional[str] = None
    """
	Transaction code of the successful transaction with which the payment for the checkout is completed.
	Read only
	"""

    transaction_id: typing.Optional[str] = None
    """
	Transaction ID of the successful transaction with which the payment for the checkout is completed.
	Read only
	"""

    transactions: typing.Optional[list[CheckoutSuccessTransaction]] = None
    """
	List of transactions related to the payment.
	Unique items only
	"""

    valid_until: typing.Optional[datetime] = None
    """
	Date and time of the checkout expiration before which the client application needs to send a processing request.If no value is present, the checkout does not have an expiration time.
	"""


CheckoutAcceptedNextStepMechanism = typing.Literal["browser", "iframe"]


class CheckoutAcceptedNextStepPayload(pydantic.BaseModel):
    """
    Contains parameters essential for form redirection. Number of object keys and their content can vary.
    """

    MD: typing.Optional[typing.Any] = None

    PaReq: typing.Optional[typing.Any] = None

    TermUrl: typing.Optional[typing.Any] = None


class CheckoutAcceptedNextStep(pydantic.BaseModel):
    """
    Required action processing 3D Secure payments.
    """

    mechanism: typing.Optional[list[CheckoutAcceptedNextStepMechanism]] = None
    """
	Indicates allowed mechanisms for redirecting an end user. If both values are provided to ensure a redirect takesplace in either.
	"""

    method: typing.Optional[str] = None
    """
	Method used to complete the redirect.
	"""

    payload: typing.Optional[CheckoutAcceptedNextStepPayload] = None
    """
	Contains parameters essential for form redirection. Number of object keys and their content can vary.
	"""

    redirect_url: typing.Optional[str] = None
    """
	Refers to a url where the end user is redirected once the payment processing completes.
	"""

    url: typing.Optional[str] = None
    """
	Where the end user is redirected.
	"""


class CheckoutAccepted(pydantic.BaseModel):
    """
    3DS Response
    """

    next_step: typing.Optional[CheckoutAcceptedNextStep] = None
    """
	Required action processing 3D Secure payments.
	"""


MandatePayloadType = typing.Literal["recurrent"]


class MandatePayload(pydantic.BaseModel):
    """
    Mandate is passed when a card is to be tokenized
    """

    type: MandatePayloadType
    """
	Indicates the mandate type
	"""

    user_agent: str
    """
	Operating system and web client used by the end-user
	"""

    user_ip: typing.Optional[str] = None
    """
	IP address of the end user. Supports IPv4 and IPv6
	"""


CardExpiryMonth = typing.Literal[
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"
]

CardType = typing.Literal[
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


class Card(pydantic.BaseModel):
    """
    __Required when payment type is `card`.__ Details of the payment card.
    """

    cvv: str
    """
	Three or four-digit card verification value (security code) of the payment card.
	Write only
	Min length: 3
	Max length: 4
	"""

    expiry_month: CardExpiryMonth
    """
	Month from the expiration time of the payment card. Accepted format is `MM`.
	Write only
	"""

    expiry_year: str
    """
	Year from the expiration time of the payment card. Accepted formats are `YY` and `YYYY`.
	Write only
	Min length: 2
	Max length: 4
	"""

    last_4_digits: str
    """
	Last 4 digits of the payment card number.
	Read only
	Min length: 4
	Max length: 4
	"""

    name: str
    """
	Name of the cardholder as it appears on the payment card.
	Write only
	"""

    number: str
    """
	Number of the payment card (without spaces).
	Write only
	"""

    type: CardType
    """
	Issuing card network of the payment card.
	Read only
	"""

    zip_code: typing.Optional[str] = None
    """
	Required five-digit ZIP code. Applicable only to merchant users in the USA.
	Write only
	Min length: 5
	Max length: 5
	"""


class Address(pydantic.BaseModel):
    """
    Profile's personal address information.
    """

    city: typing.Optional[str] = None
    """
	City name from the address.
	"""

    country: typing.Optional[str] = None
    """
	Two letter country code formatted according to [ISO3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2).
	"""

    line_1: typing.Optional[str] = None
    """
	First line of the address with details of the street name and number.
	"""

    line_2: typing.Optional[str] = None
    """
	Second line of the address with details of the building, unit, apartment, and floor numbers.
	"""

    postal_code: typing.Optional[str] = None
    """
	Postal code from the address.
	"""

    state: typing.Optional[str] = None
    """
	State name or abbreviation from the address.
	"""


class PersonalDetails(pydantic.BaseModel):
    """
    Personal details for the customer.
    """

    address: typing.Optional[Address] = None
    """
	Profile's personal address information.
	"""

    birth_date: typing.Optional[date] = None
    """
	Date of birth of the customer.
	Format: date
	"""

    email: typing.Optional[str] = None
    """
	Email address of the customer.
	"""

    first_name: typing.Optional[str] = None
    """
	First name of the customer.
	"""

    last_name: typing.Optional[str] = None
    """
	Last name of the customer.
	"""

    phone: typing.Optional[str] = None
    """
	Phone number of the customer.
	"""

    tax_id: typing.Optional[str] = None
    """
	An identification number user for tax purposes (e.g. CPF)
	Max length: 255
	"""


CheckoutProcessMixinPaymentType = typing.Literal["bancontact", "blik", "boleto", "card", "ideal"]


class CheckoutProcessMixin(pydantic.BaseModel):
    """
    Details of the payment instrument for processing the checkout.
    """

    payment_type: CheckoutProcessMixinPaymentType
    """
	Describes the payment method used to attempt processing
	"""

    card: typing.Optional[Card] = None
    """
	__Required when payment type is `card`.__ Details of the payment card.
	"""

    customer_id: typing.Optional[str] = None
    """
	__Required when `token` is provided.__ Unique ID of the customer.
	"""

    installments: typing.Optional[int] = None
    """
	Number of installments for deferred payments. Available only to merchant users in Brazil.
	Min: 1
	Max: 12
	"""

    mandate: typing.Optional[MandatePayload] = None
    """
	Mandate is passed when a card is to be tokenized
	"""

    personal_details: typing.Optional[PersonalDetails] = None
    """
	Personal details for the customer.
	"""

    token: typing.Optional[str] = None
    """
	__Required when using a tokenized card to process a checkout.__ Unique token identifying the saved payment cardfor a customer.
	"""

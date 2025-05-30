# Code generated by `py-sdk-gen`. DO NOT EDIT.
import typing
import pydantic

AccountType = typing.Literal["normal", "operator"]


class Account(pydantic.BaseModel):
    """
    Profile information.
    """

    type: typing.Optional[AccountType] = None
    """
	The role of the user.
	"""

    username: typing.Optional[str] = None
    """
	Username of the user profile.
	"""


class CountryDetails(pydantic.BaseModel):
    """
    Country Details
    """

    currency: typing.Optional[str] = None
    """
	Currency ISO 4217 code
	"""

    en_name: typing.Optional[str] = None
    """
	Country EN name
	"""

    iso_code: typing.Optional[str] = None
    """
	Country ISO code
	"""

    native_name: typing.Optional[str] = None
    """
	Country native name
	"""


class TimeoffsetDetails(pydantic.BaseModel):
    """
    TimeOffset Details
    """

    dst: typing.Optional[bool] = None
    """
	Daylight Saving Time
	"""

    offset: typing.Optional[float] = None
    """
	UTC offset
	"""

    post_code: typing.Optional[str] = None
    """
	Postal code
	"""


class AddressWithDetails(pydantic.BaseModel):
    """
    Details of the registered address.
    """

    address_line1: typing.Optional[str] = None
    """
	Address line 1
	"""

    address_line2: typing.Optional[str] = None
    """
	Address line 2
	"""

    city: typing.Optional[str] = None
    """
	City
	"""

    company: typing.Optional[str] = None
    """
	undefined
	"""

    country: typing.Optional[str] = None
    """
	Country ISO 3166-1 code
	"""

    country_details: typing.Optional[CountryDetails] = None
    """
	Country Details
	"""

    first_name: typing.Optional[str] = None
    """
	undefined
	"""

    landline: typing.Optional[str] = None
    """
	Landline number
	"""

    last_name: typing.Optional[str] = None
    """
	undefined
	"""

    post_code: typing.Optional[str] = None
    """
	Postal code
	"""

    region_code: typing.Optional[str] = None
    """
	Region code
	"""

    region_id: typing.Optional[float] = None
    """
	Country region id
	"""

    region_name: typing.Optional[str] = None
    """
	Region name
	"""

    state_id: typing.Optional[str] = None
    """
	undefined
	"""

    timeoffset_details: typing.Optional[TimeoffsetDetails] = None
    """
	TimeOffset Details
	"""


class PersonalProfile(pydantic.BaseModel):
    """
    Account's personal profile.
    """

    address: typing.Optional[AddressWithDetails] = None
    """
	Details of the registered address.
	"""

    complete: typing.Optional[bool] = None

    date_of_birth: typing.Optional[str] = None
    """
	Date of birth
	"""

    first_name: typing.Optional[str] = None
    """
	First name of the user
	"""

    last_name: typing.Optional[str] = None
    """
	Last name of the user
	"""

    mobile_phone: typing.Optional[str] = None
    """
	Mobile phone number
	"""


class LegalType(pydantic.BaseModel):
    """
    Id of the legal type of the merchant profile
    """

    description: typing.Optional[str] = None
    """
	Legal type short description
	"""

    full_description: typing.Optional[str] = None
    """
	Legal type description
	"""

    id: typing.Optional[float] = None
    """
	Unique id
	"""

    sole_trader: typing.Optional[bool] = None
    """
	Sole trader legal type if true
	"""


class BusinessOwner(pydantic.BaseModel):
    """
    BusinessOwner is a schema definition.
    """

    date_of_birth: typing.Optional[str] = None
    """
	Date of birth
	"""

    first_name: typing.Optional[str] = None
    """
	BO's first name
	"""

    landline: typing.Optional[str] = None
    """
	BO's Landline
	"""

    last_name: typing.Optional[str] = None
    """
	BO's last name of the user
	"""

    mobile_phone: typing.Optional[str] = None
    """
	Mobile phone number
	"""

    ownership: typing.Optional[float] = None
    """
	Ownership percentage
	"""


BusinessOwners = list[BusinessOwner]
"""
Business owners information.
"""


class DoingBusinessAsAddress(pydantic.BaseModel):
    """
    DoingBusinessAsAddress is a schema definition.
    """

    address_line1: typing.Optional[str] = None
    """
	Address line 1
	"""

    address_line2: typing.Optional[str] = None
    """
	Address line 2
	"""

    city: typing.Optional[str] = None
    """
	City
	"""

    country: typing.Optional[str] = None
    """
	Country ISO 3166-1 code
	"""

    post_code: typing.Optional[str] = None
    """
	Postal code
	"""

    region_id: typing.Optional[float] = None
    """
	Country region ID
	"""

    region_name: typing.Optional[str] = None
    """
	Country region name
	"""


class DoingBusinessAs(pydantic.BaseModel):
    """
    Doing Business As information
    """

    address: typing.Optional[DoingBusinessAsAddress] = None

    business_name: typing.Optional[str] = None
    """
	Doing business as name
	"""

    company_registration_number: typing.Optional[str] = None
    """
	Doing business as company registration number
	"""

    email: typing.Optional[str] = None
    """
	Doing business as email
	"""

    vat_id: typing.Optional[str] = None
    """
	Doing business as VAT ID
	"""

    website: typing.Optional[str] = None
    """
	Doing business as website
	"""


MerchantSettingsMotoPayment = typing.Literal["ENFORCED", "OFF", "ON", "UNAVAILABLE"]


class MerchantSettings(pydantic.BaseModel):
    """
    Merchant settings &#40;like \"payout_type\", \"payout_period\"&#41;
    """

    daily_payout_email: typing.Optional[bool] = None
    """
	Whether merchant will receive daily payout emails
	"""

    gross_settlement: typing.Optional[bool] = None
    """
	Whether merchant has gross settlement enabled
	"""

    monthly_payout_email: typing.Optional[bool] = None
    """
	Whether merchant will receive monthly payout emails
	"""

    moto_payment: typing.Optional[MerchantSettingsMotoPayment] = None
    """
	Whether merchant can make MOTO payments
	"""

    payout_instrument: typing.Optional[str] = None
    """
	Payout Instrument
	"""

    payout_on_demand: typing.Optional[bool] = None
    """
	Whether merchant will receive payouts on demand
	"""

    payout_on_demand_available: typing.Optional[bool] = None
    """
	Whether merchant can edit payouts on demand
	"""

    payout_period: typing.Optional[str] = None
    """
	Payout frequency
	"""

    payout_type: typing.Optional[str] = None
    """
	Payout type
	"""

    printers_enabled: typing.Optional[bool] = None
    """
	Whether to show printers in mobile app
	"""

    stone_merchant_code: typing.Optional[str] = None
    """
	Stone merchant code
	"""

    tax_enabled: typing.Optional[bool] = None
    """
	Whether to show tax in receipts &#40;saved per transaction&#41;
	"""


class VatRates(pydantic.BaseModel):
    """
    Merchant VAT rates
    """

    country: typing.Optional[str] = None
    """
	Country ISO code
	"""

    description: typing.Optional[str] = None
    """
	Description
	"""

    id: typing.Optional[float] = None
    """
	Internal ID
	"""

    ordering: typing.Optional[float] = None
    """
	Ordering
	"""

    rate: typing.Optional[float] = None
    """
	Rate
	"""


class BankAccount(pydantic.BaseModel):
    """
    BankAccount is a schema definition.
    """

    account_category: typing.Optional[str] = None
    """
	Account category - business or personal
	"""

    account_holder_name: typing.Optional[str] = None

    account_number: typing.Optional[str] = None
    """
	Account number
	"""

    account_type: typing.Optional[str] = None
    """
	Type of the account
	"""

    bank_code: typing.Optional[str] = None
    """
	Bank code
	"""

    bank_name: typing.Optional[str] = None
    """
	Bank name
	"""

    branch_code: typing.Optional[str] = None
    """
	Branch code
	"""

    created_at: typing.Optional[str] = None
    """
	Creation date of the bank account
	"""

    iban: typing.Optional[str] = None
    """
	IBAN
	"""

    primary: typing.Optional[bool] = None
    """
	The primary bank account is the one used for payouts
	"""

    status: typing.Optional[str] = None
    """
	Status in the verification process
	"""

    swift: typing.Optional[str] = None
    """
	SWIFT code
	"""


class MerchantProfile(pydantic.BaseModel):
    """
    Account's merchant profile
    """

    address: typing.Optional[AddressWithDetails] = None
    """
	Details of the registered address.
	"""

    bank_accounts: typing.Optional[list[BankAccount]] = None

    business_owners: typing.Optional[BusinessOwners] = None
    """
	Business owners information.
	"""

    company_name: typing.Optional[str] = None
    """
	Company name
	"""

    company_registration_number: typing.Optional[str] = None
    """
	Company registration number
	"""

    country: typing.Optional[str] = None
    """
	Merchant country code formatted according to [ISO3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) &#40;forinternal usage only&#41;
	"""

    doing_business_as: typing.Optional[DoingBusinessAs] = None
    """
	Doing Business As information
	"""

    extdev: typing.Optional[bool] = None
    """
	True if the merchant is extdev
	"""

    legal_type: typing.Optional[LegalType] = None
    """
	Id of the legal type of the merchant profile
	"""

    locale: typing.Optional[str] = None
    """
	Merchant locale &#40;for internal usage only&#41;
	"""

    merchant_category_code: typing.Optional[str] = None
    """
	Merchant category code
	"""

    merchant_code: typing.Optional[str] = None
    """
	Unique identifying code of the merchant profile
	"""

    mobile_phone: typing.Optional[str] = None
    """
	Mobile phone number
	"""

    nature_and_purpose: typing.Optional[str] = None
    """
	Nature and purpose of the business
	"""

    payout_zone_migrated: typing.Optional[bool] = None
    """
	True if the payout zone of this merchant is migrated
	"""

    permanent_certificate_access_code: typing.Optional[str] = None
    """
	Permanent certificate access code &#40;Portugal&#41;
	"""

    settings: typing.Optional[MerchantSettings] = None
    """
	Merchant settings &#40;like \"payout_type\", \"payout_period\"&#41;
	"""

    vat_id: typing.Optional[str] = None
    """
	Vat ID
	"""

    vat_rates: typing.Optional[VatRates] = None
    """
	Merchant VAT rates
	"""

    website: typing.Optional[str] = None
    """
	Website
	"""


class AppSettings(pydantic.BaseModel):
    """
    Mobile app settings
    """

    advanced_mode: typing.Optional[str] = None
    """
	Advanced mode.
	"""

    barcode_scanner: typing.Optional[str] = None
    """
	Barcode scanner.
	"""

    cash_payment: typing.Optional[str] = None
    """
	Cash payment.
	"""

    checkout_preference: typing.Optional[str] = None
    """
	Checkout preference
	"""

    expected_max_transaction_amount: typing.Optional[float] = None
    """
	Expected max transaction amount.
	"""

    include_vat: typing.Optional[bool] = None
    """
	Include vat.
	"""

    manual_entry: typing.Optional[str] = None
    """
	Manual entry.
	"""

    manual_entry_tutorial: typing.Optional[bool] = None
    """
	Manual entry tutorial.
	"""

    mobile_payment: typing.Optional[str] = None
    """
	Mobile payment.
	"""

    mobile_payment_tutorial: typing.Optional[bool] = None
    """
	Mobile payment tutorial.
	"""

    reader_payment: typing.Optional[str] = None
    """
	Reader payment.
	"""

    referral: typing.Optional[str] = None
    """
	Referral.
	"""

    tax_enabled: typing.Optional[bool] = None
    """
	Tax enabled.
	"""

    terminal_mode_tutorial: typing.Optional[bool] = None
    """
	Terminal mode tutorial.
	"""

    tip_rates: typing.Optional[list[float]] = None
    """
	Tip rates.
	"""

    tipping: typing.Optional[str] = None
    """
	Tipping.
	"""


class Permissions(pydantic.BaseModel):
    """
    User permissions
    """

    create_moto_payments: typing.Optional[bool] = None
    """
	Create MOTO payments
	"""

    create_referral: typing.Optional[bool] = None
    """
	Create referral
	"""

    full_transaction_history_view: typing.Optional[bool] = None
    """
	Can view full merchant transaction history
	"""

    refund_transactions: typing.Optional[bool] = None
    """
	Refund transactions
	"""


class MerchantAccount(pydantic.BaseModel):
    """
    Details of the merchant account.
    """

    account: typing.Optional[Account] = None
    """
	Profile information.
	"""

    app_settings: typing.Optional[AppSettings] = None
    """
	Mobile app settings
	"""

    is_migrated_payleven_br: typing.Optional[bool] = None
    """
	Merchant comes from payleven BR migration
	"""

    merchant_profile: typing.Optional[MerchantProfile] = None
    """
	Account's merchant profile
	"""

    permissions: typing.Optional[Permissions] = None
    """
	User permissions
	"""

    personal_profile: typing.Optional[PersonalProfile] = None
    """
	Account's personal profile.
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

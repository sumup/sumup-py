from sumup import Sumup, APIError
from sumup.checkouts.resource import CreateCheckoutBody, ListCheckoutsParams

client = Sumup()

merchant = client.merchant.get()
assert merchant is not None
print("Your merchant account: {merchant}")

readers = client.readers.list(merchant.merchant_profile.merchant_code)
print(readers)

transactions = client.checkouts.list(
    ListCheckoutsParams(checkout_reference="1231"), headers={"Foo": "Bar"}
)
print(transactions)

try:
    checkout = client.checkouts.create(
        CreateCheckoutBody(
            merchant_code=merchant.merchant_profile.merchant_code,
            amount=100.50,
            checkout_reference="unique-checkout-ref-123",
            currency="EUR",
        )
    )
    print(checkout)
except APIError as e:
    print(f"Failed to create checkout: {e} ({e.status} - {e.body})")

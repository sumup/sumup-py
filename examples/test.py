from sumup import Sumup
from sumup.checkouts.resource import ListCheckoutsParams, CreateCheckoutBody

client = Sumup()

merchant = client.merchant.get()
print(merchant)


merchant = client.readers.list(merchant.merchant_profile.merchant_code)
print(merchant)

transactions = client.checkouts.list(
    ListCheckoutsParams(checkout_reference="1231"), headers={"Foo": "Bar"}
)
print(transactions)

checkout = client.checkouts.create(
    CreateCheckoutBody(
        merchant_code=merchant.merchant_profile.merchant_code,
        amount=100.50,
        checkout_reference="unique-checkout-ref-123",
        currency="EUR",
    )
)
print(checkout)

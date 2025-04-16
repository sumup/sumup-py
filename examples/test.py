from sumup import Sumup
from sumup.checkouts.resource import ListCheckoutsParams

client = Sumup()

merchant = client.merchant.get()
print(merchant)


merchant = client.readers.list(merchant.merchant_profile.merchant_code)
print(merchant)

transactions = client.checkouts.list(
    ListCheckoutsParams(checkout_reference="1231"), headers={"Foo": "Bar"}
)
print(transactions)

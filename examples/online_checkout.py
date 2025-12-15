import os
import uuid

from sumup import Sumup
from sumup.checkouts import CreateCheckoutBody, Currency


def main() -> None:
    client = Sumup()

    merchant_code = os.environ["SUMUP_MERCHANT_CODE"]
    checkout_reference = f"online-example-{uuid.uuid4().hex}"

    checkout = client.checkouts.create(
        CreateCheckoutBody(
            amount=10.0,
            currency=Currency.EUR,
            checkout_reference=checkout_reference,
            merchant_code=merchant_code,
            description="sumup-py online checkout example",
        )
    )

    print(
        f"Checkout {checkout.id} created for {checkout.amount} "
        f"{checkout.currency} (reference={checkout.checkout_reference})"
    )


if __name__ == "__main__":
    main()

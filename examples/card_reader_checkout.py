import os
import asyncio

from sumup import AsyncSumup
from sumup.readers.resource import CreateReaderCheckoutBody, CreateReaderCheckoutBodyTotalAmount


async def main():
    client = AsyncSumup()
    merchant_code = os.environ["SUMUP_MERCHANT_CODE"]

    readers = await client.readers.list(merchant_code)
    reader = readers.items[0]

    checkout = await client.readers.create_checkout(
        merchant_code,
        reader.id,
        CreateReaderCheckoutBody(
            total_amount=CreateReaderCheckoutBodyTotalAmount(
                currency="EUR",
                minor_unit=2,
                value=1000,
            ),
            description="sumup-py card reader checkout example",
        ),
    )

    print(checkout)


if __name__ == "__main__":
    asyncio.run(main())

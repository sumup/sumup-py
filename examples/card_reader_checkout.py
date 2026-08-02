# /// script
# requires-python = ">=3.10"
# dependencies = []
# [tool.ty.environment]
# extra-paths = [".."]
# ///
"""Run from the repository root: uv run --with-editable . examples/card_reader_checkout.py

Set SUMUP_API_KEY and SUMUP_MERCHANT_CODE before running.
"""

import asyncio
import os

from sumup import AsyncSumup


async def main():
    client = AsyncSumup()
    merchant_code = os.environ["SUMUP_MERCHANT_CODE"]

    readers = await client.readers.list(merchant_code)
    reader = readers.items[0]

    checkout = await client.readers.create_checkout(
        merchant_code=merchant_code,
        reader_id=reader.id,
        total_amount={"currency": "EUR", "minor_unit": 2, "value": 1000},
        description="sumup-py card reader checkout example",
    )

    print(checkout)


if __name__ == "__main__":
    asyncio.run(main())

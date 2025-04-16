import asyncio
from sumup import AsyncSumup


async def main():
    client = AsyncSumup()

    merchant = await client.merchant.get()

    print(merchant)


if __name__ == "__main__":
    asyncio.run(main())

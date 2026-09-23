import asyncio
import httpx


async def get_product(client, i):

    response = await client.get(
        "http://localhost:8004/products/101"
    )

    print(f"Request {i}: {response.json()}")


async def main():

    async with httpx.AsyncClient() as client:

        tasks = [
            get_product(client, i)
            for i in range(1, 11)
        ]

        await asyncio.gather(*tasks)


asyncio.run(main())
import asyncio
import httpx


async def make_payment(client, request_number):

    response = await client.post(
        "http://localhost:8003/payments",
        params={
            "id": 6000,
            "amount": 75000,
            "idempotency_key": "payment-order-6000"
        }
    )

    print(
        f"Request {request_number}: "
        f"{response.status_code} "
        f"{response.json()}"
    )


async def main():

    async with httpx.AsyncClient() as client:

        tasks = [
            make_payment(client, i)
            for i in range(1, 11)
        ]

        await asyncio.gather(*tasks)


asyncio.run(main())


# import asyncio
# import httpx


# async def make_payment(client, order_id):

#     response = await client.post(
#         "http://localhost:8003/payments",
#         json={
#             "Idempotency_id": order_id,
#             "amount": 75000
#         }
#     )

#     print(response.status_code, response.json())


# async def main():

#     async with httpx.AsyncClient() as client:

#         tasks = [
#             make_payment(client, 5001)
#             for _ in range(5)
#         ]

#         await asyncio.gather(*tasks)


# asyncio.run(main())
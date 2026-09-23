from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx

from circuit_breaker import CircuitBreaker
import asyncio

app = FastAPI(title="Orders App")


USER_SERVICE_URL = "http://localhost:8001"


user_breaker = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=10
)


async def get_user_with_retry(user_id: int):

    max_retries = 4

    async with httpx.AsyncClient() as client:

        for attempt in range(1, max_retries + 1):

            try:
                print(f"User API attempt {attempt}")
                response = await client.get(
                    f"{USER_SERVICE_URL}/users/{user_id}",
                    timeout=3.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                print(f"User service timeout on attempt {attempt}")
                if attempt == max_retries:
                    raise HTTPException(
                        status_code=504,
                        detail="User service timeout after retries"
                    )
                delay = 2 ** (attempt - 1)
                print(f"Retrying after {delay} seconds...")
                await asyncio.sleep(delay)
            except httpx.HTTPStatusError as exc:
                print(f"User service returned HTTP {exc.response.status_code}")
                # Don't retry 4xx errors
                if 400 <= exc.response.status_code < 500:
                    raise HTTPException(
                        status_code=exc.response.status_code,
                        detail="User request failed"
                    )
                # Retry 5xx errors
                if attempt == max_retries:
                    raise HTTPException(
                        status_code=502,
                        detail="User service unavailable"
                    )

                delay = 2 ** (attempt - 1)
                await asyncio.sleep(delay)
            except httpx.RequestError as exc:
                print(f"User service connection error: {exc}")
                if attempt == max_retries:
                    raise HTTPException(
                        status_code=502,
                        detail="User service unavailable"
                    )
                delay = 2 ** (attempt - 1)
                await asyncio.sleep(delay)


async def call_user_service(client, user_id):
    if not user_breaker.can_execute():
        print("Circuit OPEN - not calling User Service")
        raise HTTPException(status_code=503, detail="User service temporarily unavailable")

    try:
        print(f"Calling User Service for user {user_id}")

        response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}", timeout=3.0)
        response.raise_for_status()
        user = response.json()
        user_breaker.record_success()
        return user
    except httpx.TimeoutException:
        print("User Service timeout")
        user_breaker.record_failure()
        raise HTTPException(
            status_code=504,
            detail="User service timeout"
        )
    except httpx.RequestError as exc:
        print(f"User Service connection error: {exc}")
        user_breaker.record_failure()
        raise HTTPException(
            status_code=502,
            detail="User service unavailable"
        )

    except httpx.HTTPStatusError as exc:
        print(f"User Service HTTP error: {exc.response.status_code}")
        user_breaker.record_failure()
        raise HTTPException(
            status_code=502,
            detail="User service error"
        )

class Order(BaseModel):
    order_id: int
    user_id: int

# @app.get("/orders")
# async def get_order(order: Order):

#     user = await get_user_with_retry(order.user_id)
    
#     return {
#         "order_id": order.order_id,
#         "product": "Laptop",
#         "amount": 75000,
#         "user": user
#     }

@app.post("/orders")
async def create_order(order: Order):

    async with httpx.AsyncClient() as client:
        user = await call_user_service(client, order.user_id)

    return {
        "order_id": order.order_id,
        "product": "Laptop",
        "amount": 75000,
        "user": user
    }

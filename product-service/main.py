from fastapi import FastAPI
import redis.asyncio as redis
import json
import asyncio
from redis.exceptions import RedisError

app = FastAPI(title="Product Service")

product_locks = {}

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)


products = {
    100: {
        "id": 100,
        "name": "Laptop",
        "price": 75000
    },
    101: {
        "id": 101,
        "name": "Mouse",
        "price": 15000
    }
}

product_locks = {}

def get_product_lock(product_id: int):
    if product_id not in product_locks:
        product_locks[product_id] = asyncio.Lock()

    return product_locks[product_id]

@app.get("/products/{product_id}")
async def get_product(product_id: int):

    cache_key = f"product:{product_id}"

    # -------------------------
    # 1. Check Redis
    # -------------------------
    try:
        cached_product = await redis_client.get(cache_key)
        if cached_product:
            print(f"CACHE HIT → {cache_key}")
            return json.loads(cached_product)
    except RedisError as e:
        print(f"REDIS UNAVAILABLE → {e}")

    # -------------------------
    # 2. Cache MISS
    # -------------------------
    print(f"CACHE MISS → {cache_key}")

    lock = get_product_lock(product_id)

    async with lock:

        try:
            # IMPORTANT:
            # Check Redis AGAIN after acquiring lock
            cached_product = await redis_client.get(cache_key)

            if cached_product:
                print(f"CACHE HIT AFTER LOCK → {cache_key}")
                return json.loads(cached_product)
        except RedisError as e:
            print(f"REDIS UNAVAILABLE → {e}")

        print(f"DB CALL START → {product_id}")

        await asyncio.sleep(3)

        product = products.get(product_id)

        if not product:
            return {"error": "Product not found"}

        print(f"DB CALL END → {product_id}")

        # -------------------------
        # 3. Store in Redis
        # -------------------------
        try:
            await redis_client.set(
                cache_key,
                json.dumps(product),
                ex=30
            )
            print(f"Stored in Redis → {cache_key}")
        except RedisError as e:
            print(f"REDIS SET FAILED → {e}")

        # -------------------------
        # 4. Return product
        # -------------------------
        return product

@app.put("/products/{product_id}")
async def update_product(product_id: int, price: int):

    product = products.get(product_id)

    if not product:
        return {"error": "Product not found"}

    # Update source
    product["price"] = price

    # Invalidate cache
    cache_key = f"product:{product_id}"
    try:
       await redis_client.delete(cache_key)
       print(f"CACHE INVALIDATED → {cache_key}")
    except RedisError as e:
        print(f"REDIS DELETE FAILED → {e}")

    return product
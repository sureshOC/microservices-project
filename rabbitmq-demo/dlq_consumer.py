import asyncio
import aio_pika

RABBITMQ_URI = "amqp://guest:guest@localhost/"

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URI)
    channel = await connection.channel()

    queue = await channel.declare_queue("orders_queue", durable=True, arguments={"x-dead-letter-exchange": "orders_dlx", "x-dead-letter-routing-key": "failed"})
    print("DLQ consumer started")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            print(f"Received: {message.body.decode()}")
            await message.nack(requeue=False)

asyncio.run(main())
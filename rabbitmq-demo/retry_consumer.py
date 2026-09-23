import asyncio
import aio_pika

RABBITMQ_URI = "amqp://guest:guest@localhost/"
MAX_RETRIES = 3

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URI)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)
    main_queue = await channel.declare_queue("orders_queue", durable=True, arguments={"x-dead-letter-exchange": "orders_dlx", "x-dead-letter-routing-key": "failed"})
    retry_exchange = await channel.declare_exchange("orders_retry_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
    dlx = await channel.declare_exchange("orders_dlx", aio_pika.ExchangeType.DIRECT, durable=True)
    print("Retry consumer started")
    async with main_queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process(requeue=False):
                retry_count = int(message.headers.get("x-retry-count", 0))
                print(f"Processing {message.body.decode()}, attempt {retry_count + 1}")
                await asyncio.sleep(1)
                if retry_count < MAX_RETRIES:
                    retry_message = aio_pika.Message(body=message.body, headers={**message.headers, "x-retry-count": retry_count + 1}, delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
                    await retry_exchange.publish(retry_message, routing_key="retry")
                    print(f"Scheduled retry {retry_count + 1}")
                else:
                    await dlx.publish(aio_pika.Message(body=message.body, headers=message.headers, delivery_mode=aio_pika.DeliveryMode.PERSISTENT), routing_key="failed")
                    print("Retry limit reached; sent to DLQ")

asyncio.run(main())

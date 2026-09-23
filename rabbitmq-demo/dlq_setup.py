import asyncio
import aio_pika

RABBITMQ_URI = "amqp://guest:guest@localhost/"

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URI)
    channel = await connection.channel()
    

    dlx = await channel.declare_exchange("orders_dlx", aio_pika.ExchangeType.DIRECT, durable=True)
    dlq = await channel.declare_queue("orders_dlq", durable=True)
    await dlq.bind(dlx, routing_key="failed")

    exchange = await channel.declare_exchange("orders_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
    orders_queue = await channel.declare_queue("orders_queue", durable=True, arguments={"x-dead-letter-exchange": "orders_dlx", "x-dead-letter-routing-key": "failed"})
    await orders_queue.bind(exchange, routing_key="order.created")

    print("DLQ setup completed")
    await connection.close()

asyncio.run(main())
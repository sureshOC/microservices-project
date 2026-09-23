import asyncio
import aio_pika

RABBITMQ_URI = "amqp://guest:guest@localhost/"

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URI)
    channel = await connection.channel()
    main_exchange = await channel.declare_exchange("orders_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
    retry_exchange = await channel.declare_exchange("orders_retry_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
    dlx = await channel.declare_exchange("orders_dlx", aio_pika.ExchangeType.DIRECT, durable=True)
    main_queue = await channel.declare_queue("orders_queue", durable=True, arguments={"x-dead-letter-exchange": "orders_dlx", "x-dead-letter-routing-key": "failed"})
    retry_queue = await channel.declare_queue("orders_retry_queue", durable=True, arguments={"x-message-ttl": 5000, "x-dead-letter-exchange": "orders_exchange", "x-dead-letter-routing-key": "order.created"})
    dlq = await channel.declare_queue("orders_dlq", durable=True)
    await main_queue.bind(main_exchange, routing_key="order.created")
    await retry_queue.bind(retry_exchange, routing_key="retry")
    await dlq.bind(dlx, routing_key="failed")
    print("Retry topology setup completed")
    await connection.close()

asyncio.run(main())
import asyncio
import aio_pika

RABBITMQ_URI = "amqp://guest:guest@localhost/"

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URI)
    channel = await connection.channel(publisher_confirms=True, on_return_raises=True)
    exchange = await channel.declare_exchange("confirm_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
    queue = await channel.declare_queue("confirm_queue", durable=True)
    await queue.bind(exchange, routing_key="confirm.test")
    message = aio_pika.Message(body=b"Confirmed Order 8001", delivery_mode=aio_pika.DeliveryMode.PERSISTENT)
    #confirmation = await exchange.publish(message, routing_key="confirm.test", mandatory=True)
    confirmation = await exchange.publish(message, routing_key="confirm.missing", mandatory=True)
    print(f"Publisher confirmation received: {confirmation}")
    await connection.close()

asyncio.run(main())

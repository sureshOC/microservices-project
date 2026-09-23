import asyncio
import aio_pika

RABBITMQ_URI = "amqp://guest:guest@localhost/"

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URI)
    channel = await connection.channel()
    exchange = await channel.declare_exchange("orders_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
 

    message = aio_pika.Message(body=b"Order 9999")
    await exchange.publish(message, routing_key="order.created")
    print("Order sent")
    await connection.close()

asyncio.run(main())


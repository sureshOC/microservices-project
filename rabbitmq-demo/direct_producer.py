import asyncio
import aio_pika

RABITMQ_URI = 'amqp://guest:guest@localhost/'
QUE_NAME = 'orders_queue'

ROUTING_KEY = 'orders.created'
ROUTING_KEY_CANCEL = 'orders.cancelled'

async def main():

    connection = await aio_pika.connect_robust(RABITMQ_URI)

    channel = await connection.channel()

    # Create exchange
    exchange = await channel.declare_exchange("orders_exchange", aio_pika.ExchangeType.DIRECT, durable=True)

    # Create queue
    queue = await channel.declare_queue(QUE_NAME, durable=True)

    # Connect queue to exchange
    await queue.bind(exchange, routing_key=ROUTING_KEY)
    # await queue.bind(exchange, routing_key=ROUTING_KEY_CANCEL)


    message = aio_pika.Message(body=b'Oder 1001 created!')
    await exchange.publish(message, routing_key=ROUTING_KEY)
    # await exchange.publish(message, routing_key=ROUTING_KEY_CANCEL)

    print("Order message sent!")

    await connection.close()


asyncio.run(main())


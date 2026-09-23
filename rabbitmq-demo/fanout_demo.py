import asyncio
import aio_pika

RABITMQ_URI = 'amqp://guest:guest@localhost/'

async def main():
    connection = await aio_pika.connect_robust(RABITMQ_URI)
    channel = await connection.channel()

    # Create exchange
    exchange = await channel.declare_exchange("events_exchange", aio_pika.ExchangeType.FANOUT, durable=True)

    # Create queue
    orders_queue = await channel.declare_queue("fanout_orders_queue", durable=True)
    audit_queue = await channel.declare_queue("fanout_audit_queue", durable=True)
    notification_queue = await channel.declare_queue("fanout_notification_queue", durable=True)


    # Connect queue to exchange or bind queues to the exchange?
    await orders_queue.bind(exchange)
    await audit_queue.bind(exchange)
    await notification_queue.bind(exchange)

    message = aio_pika.Message(body=b'Hello, World!')
    await exchange.publish(message, routing_key='THIS_IS_COMPLETELY_DIFFERENT') # routing_key is ignored for fanout exchange
    print("Message sent!")

    await connection.close()

asyncio.run(main())

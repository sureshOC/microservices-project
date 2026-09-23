import asyncio
import aio_pika

RABITMQ_URI = 'amqp://guest:guest@localhost/'

async def main():
    connection = await aio_pika.connect_robust(RABITMQ_URI)
    channel = await connection.channel()

    # Create exchange
    exchange = await channel.declare_exchange("events_topic_exchange", aio_pika.ExchangeType.TOPIC, durable=True)

    # Create queue
    order_queue = await channel.declare_queue("topic_orders_queue", durable=True)
    payment_queue = await channel.declare_queue("topic_payments_queue", durable=True)
    all_order_events_queue = await channel.declare_queue("topic_all_order_events_queue", durable=True)

    await order_queue.bind(exchange, routing_key="order.*")
    await payment_queue.bind(exchange, routing_key="payment.*")
    await all_order_events_queue.bind(exchange, routing_key="order.#")
    
    # Send messages with different routing keys
    message1 = aio_pika.Message(body=b"Order 3001 Created")
    await exchange.publish(message1, routing_key="order.created")

    message2 = aio_pika.Message(body=b"Order 3001 Updated")
    await exchange.publish(message2, routing_key="order.updated")

    message3 = aio_pika.Message(body=b"Payment 3001 Failed")
    await exchange.publish(message3, routing_key="payment.failed")
    
    message4 = aio_pika.Message(body=b"Order Payment 3001 Created")
    await exchange.publish(message4, routing_key="order.payment.created")
    print("Topic messages sent!")


    # close the connection
    await connection.close()

asyncio.run(main())
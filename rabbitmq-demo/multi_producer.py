import asyncio
import aio_pika

RABITMQ_URI = 'amqp://guest:guest@localhost/'
ORDERS_QUE = 'orders_queue'
PAYMENTS_QUE = 'payments_queue'

ORDERS_ROUTING_KEY = 'orders.created '
PAYMENTS_ROUTING_KEY = 'payments.created '


async def main():

    connection = await aio_pika.connect_robust(RABITMQ_URI)
    channel = await connection.channel()
    # Create exchange
    exchange = await channel.declare_exchange("orders_exchange", aio_pika.ExchangeType.DIRECT, durable=True)

    # Create queue
    orders_queue = await channel.declare_queue(ORDERS_QUE, durable=True)
    payments_queue = await channel.declare_queue(PAYMENTS_QUE, durable=True)
    audit_queue = await channel.declare_queue("audit_queue", durable=True)

    # Connect queue to exchange
    await orders_queue.bind(exchange, routing_key=ORDERS_ROUTING_KEY)
    await payments_queue.bind(exchange, routing_key=PAYMENTS_ROUTING_KEY)
    await audit_queue.bind(exchange, routing_key=ORDERS_ROUTING_KEY) # same routing key used for orders and audit queue


    message = aio_pika.Message(body=b'Oder 1001 created!')
    await exchange.publish(message, routing_key=ORDERS_ROUTING_KEY) # the message will be sent to both orders and audit queue since they are bound to the same routing key
    print("Order message sent!")
    message = aio_pika.Message(body=b'payment 1001 created!')
    await exchange.publish(message, routing_key=PAYMENTS_ROUTING_KEY)
    print("Payment message sent!")

    # message = aio_pika.Message(body=b'audit 1001 created!')
    # await exchange.publish(message, routing_key=ORDERS_ROUTING_KEY)
    # print('Audit message sent!')
    await connection.close()


asyncio.run(main())


import asyncio
import json
import aio_pika
from rabbitmq_topology import EXCHANGE_NAME

RABBITMQ_URL = "amqp://guest:guest@localhost/"

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel(publisher_confirms=True, on_return_raises=True)
    exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True)
    event = {"event_id": "failure-test-001", "order_id": "order-failure-001", "customer_id": 1, "item": "TestFailure", "quantity": 1, "simulate_failure": True}
    message = aio_pika.Message(body=json.dumps(event).encode(), content_type="application/json", delivery_mode=aio_pika.DeliveryMode.PERSISTENT, message_id=event["event_id"])
    await exchange.publish(message, routing_key="order.created", mandatory=True)
    print("Published intentional failure test event")
    await connection.close()

if __name__ == "__main__":
    asyncio.run(main())

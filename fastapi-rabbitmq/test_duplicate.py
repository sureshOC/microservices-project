import asyncio
import json
import aio_pika

RABBITMQ_URL = "amqp://guest:guest@localhost/"

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel(publisher_confirms=True)
    exchange = await channel.declare_exchange("fastapi_orders_exchange", aio_pika.ExchangeType.DIRECT, durable=True)

    event = {"event_id": "duplicate-test-001", "order_id": "order-duplicate-001", "customer_id": 1, "item": "Keyboard", "quantity": 1}

    for attempt in range(2):
        message = aio_pika.Message(body=json.dumps(event).encode(), content_type="application/json", delivery_mode=aio_pika.DeliveryMode.PERSISTENT, message_id=event["event_id"])
        await exchange.publish(message, routing_key="order.created", mandatory=True)
        print(f"Published copy {attempt + 1}: {event['event_id']}")

    await connection.close()

if __name__ == "__main__":
    asyncio.run(main())

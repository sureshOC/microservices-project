import asyncio, json, aio_pika

RABBITMQ_URI = "amqp://guest:guest@localhost/"

async def main():
    connection = await aio_pika.connect_robust(RABBITMQ_URI)
    channel = await connection.channel(publisher_confirms=True)
    exchange = await channel.declare_exchange("idempotency_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
    event = {"event_id": "evt-8001", "order_id": 8001, "amount": 100}
    for attempt in range(2):
        message = aio_pika.Message(body=json.dumps(event).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT, message_id=event["event_id"])
        confirmation = await exchange.publish(message, routing_key="order.created", mandatory=True)
        print(f"Published copy {attempt + 1}: {event['event_id']} | Confirmation: {confirmation}")
    await connection.close()

if __name__ == "__main__":
    asyncio.run(main())

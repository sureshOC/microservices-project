import asyncio
import json
import aio_pika
from database import init_db, process_order
from rabbitmq_topology import setup_topology, QUEUE_NAME, EXCHANGE_NAME

RABBITMQ_URL = "amqp://guest:guest@localhost/"
MAX_RETRIES = 3

async def main():
    init_db()
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel(publisher_confirms=True, on_return_raises=True)
    await channel.set_qos(prefetch_count=1)
    _, retry_exchange = await setup_topology(channel)
    queue = await channel.get_queue(QUEUE_NAME)
    print("Reliable order consumer waiting for messages...")

    try:
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                try:
                    event = json.loads(message.body.decode())
                    retry_count = int((message.headers or {}).get("x-retry-count", 0))
                    print(f"Received event {event.get('event_id')} | Attempt {retry_count + 1}")

                    if event.get("simulate_failure"):
                        raise RuntimeError("Intentional test failure")

                    await asyncio.to_thread(process_order, event)
                    await message.ack()
                    print(f"ACK: {event['order_id']}")

                except Exception as exc:
                    retry_count = int((message.headers or {}).get("x-retry-count", 0))
                    print(f"Processing failed: {exc}")

                    if retry_count < MAX_RETRIES:
                        headers = dict(message.headers or {})
                        headers["x-retry-count"] = retry_count + 1
                        retry_message = aio_pika.Message(body=message.body, headers=headers, content_type=message.content_type, delivery_mode=aio_pika.DeliveryMode.PERSISTENT, message_id=message.message_id, correlation_id=message.correlation_id)
                        try:
                            await retry_exchange.publish(retry_message, routing_key="retry", mandatory=True)
                            await message.ack()
                            print(f"Retry scheduled: {retry_count + 1}/{MAX_RETRIES}")
                        except Exception as publish_error:
                            print(f"Retry publish failed: {publish_error}")
                            await message.nack(requeue=True)
                    else:
                        await message.nack(requeue=False)
                        print("Maximum retries reached; message sent to DLQ")

    finally:
        await connection.close()

if __name__ == "__main__":
    asyncio.run(main())

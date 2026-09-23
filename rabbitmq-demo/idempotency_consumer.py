import asyncio, json, sqlite3, aio_pika

RABBITMQ_URI = "amqp://guest:guest@localhost/"
DB_PATH = "rabbitmq_idempotency.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS processed_events (event_id TEXT PRIMARY KEY, processed_at TEXT DEFAULT CURRENT_TIMESTAMP)")
        conn.execute("CREATE TABLE IF NOT EXISTS orders (order_id INTEGER PRIMARY KEY, status TEXT NOT NULL, processing_count INTEGER NOT NULL DEFAULT 0)")

def process_event(event):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("INSERT OR IGNORE INTO processed_events(event_id) VALUES (?)", (event["event_id"],))
        if cursor.rowcount == 0:
            print(f"Duplicate event skipped: {event['event_id']}")
            return
        conn.execute("INSERT INTO orders(order_id, status, processing_count) VALUES (?, ?, 1) ON CONFLICT(order_id) DO UPDATE SET status=excluded.status, processing_count=orders.processing_count+1", (event["order_id"], "CREATED"))
        print(f"Order processed: {event['order_id']} | Event: {event['event_id']}")

async def main():
    init_db()
    connection = await aio_pika.connect_robust(RABBITMQ_URI)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)
    exchange = await channel.declare_exchange("idempotency_exchange", aio_pika.ExchangeType.DIRECT, durable=True)
    queue = await channel.declare_queue("idempotency_queue", durable=True)
    await queue.bind(exchange, routing_key="order.created")
    print("Idempotency consumer is waiting for messages...")
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process(requeue=True):
                event = json.loads(message.body.decode())
                process_event(event)

if __name__ == "__main__":
    asyncio.run(main())

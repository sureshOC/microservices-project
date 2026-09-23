import aio_pika

EXCHANGE_NAME = "fastapi_orders_exchange"
QUEUE_NAME = "fastapi_orders_queue_v2"
RETRY_EXCHANGE = "fastapi_orders_retry_exchange"
RETRY_QUEUE = "fastapi_orders_retry_queue"
DLX_EXCHANGE = "fastapi_orders_dlx"
DLQ_QUEUE = "fastapi_orders_dlq"
ROUTING_KEY = "order.created"

async def setup_topology(channel):
    exchange = await channel.declare_exchange(EXCHANGE_NAME, aio_pika.ExchangeType.DIRECT, durable=True)
    retry_exchange = await channel.declare_exchange(RETRY_EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True)
    dlx_exchange = await channel.declare_exchange(DLX_EXCHANGE, aio_pika.ExchangeType.DIRECT, durable=True)

    queue = await channel.declare_queue(QUEUE_NAME, durable=True, arguments={"x-dead-letter-exchange": DLX_EXCHANGE, "x-dead-letter-routing-key": "failed"})
    await queue.bind(exchange, routing_key=ROUTING_KEY)

    retry_queue = await channel.declare_queue(RETRY_QUEUE, durable=True, arguments={"x-message-ttl": 5000, "x-dead-letter-exchange": EXCHANGE_NAME, "x-dead-letter-routing-key": ROUTING_KEY})
    await retry_queue.bind(retry_exchange, routing_key="retry")

    dlq = await channel.declare_queue(DLQ_QUEUE, durable=True)
    await dlq.bind(dlx_exchange, routing_key="failed")

    return exchange, retry_exchange

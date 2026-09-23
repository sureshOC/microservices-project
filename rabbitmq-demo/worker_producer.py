import asyncio
import aio_pika

RABITMQ_URI = 'amqp://guest:guest@localhost/'
async def main():
    connection = await aio_pika.connect_robust(RABITMQ_URI)
    channel = await connection.channel()

    # exchange
    exchange = await channel.declare_exchange('worker_exchange', aio_pika.ExchangeType.DIRECT, durable=True)
    queue = await channel.declare_queue('worker_queue', durable=True)
    await queue.bind(exchange, routing_key="work")

    for i in range(1, 11):
        message = aio_pika.Message(body=f'Task-{i}'.encode())
        await exchange.publish(message, routing_key="work")
        print(f"Sent Task-{i}")
        
    await connection.close()

asyncio.run(main())

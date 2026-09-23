import asyncio
import aio_pika

RABITMQ_URI = 'amqp://guest:guest@localhost/'
async def main():
    connection = await aio_pika.connect_robust(RABITMQ_URI)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=2)
    queue = await channel.declare_queue("worker_queue", durable=True)

    print("Worker started")
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                print(f"Worker received: {message.body.decode()}")
                await asyncio.sleep(1) # 10sec for worker -1 and 1sec for worker-2

asyncio.run(main())
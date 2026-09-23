# write a code for consumer

import asyncio
import aio_pika


RABITMQ_URI = 'amqp://guest:guest@localhost/'


async def main():
    connection = await aio_pika.connect_robust(RABITMQ_URI)

    channal = await connection.channel()

    que = await channal.declare_queue('test_que', durable=True)

    print('Waiting for the messages...!!')

    async with que.iterator() as que_iter:
        async for message in que_iter:
            async with message.process():
                print(f'Recieved Message: {message.body.decode()}')
                await asyncio.sleep(10)
                # raise Exception("Consumer crashed!")
                # await message.nack(requeue=True)
                # await message.nack(requeue=False)
                # await message.ack()
                # print('Nacked')

    # connection.close()

asyncio.run(main())

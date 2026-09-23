import asyncio
import aio_pika

RABITMQ_URI = 'amqp://guest:guest@localhost/'

async def main():

    connection = await aio_pika.connect_robust(RABITMQ_URI)

    channal = await connection.channel()

    que = await channal.declare_queue('test_que', durable=True)

    message = aio_pika.Message(body=b'Hello RabitMQ!')

    await channal.default_exchange.publish(message, 
                                           routing_key=que.name)

    print("Message sent!")

    await connection.close()


asyncio.run(main())


# import time

# #def time_cal(n, delay):
# #    print(f'number: {n} time_cal started and waited for {delay}')
# #    time.sleep(delay)
# #    print(f'number: {n} time_cal ended')


# #time_cal(1,2)
# #time_cal(2,4)
# import asyncio

# async def time_cal(n, delay):
#     print(f'number: {n} time_cal started and waited for {delay}')
#     await asyncio.sleep(delay)
#     print(f'number: {n} time_cal ended')
#     #math 2


# async def main():
#  #await time_cal(1,2)
#  #await time_cal(2,4)
#  await asyncio.gather(time_cal(1,1), time_cal(2, 1))

# asyncio.run(main())


import asyncio
import time

async def task1():
    print("Task 1 started")
    await asyncio.sleep(3)
    print("Task 1 completed")

async def task2():
    print("Task 2 started")
    # await asyncio.sleep(1)
    time.sleep(3)
    print("Task 2 completed")

async def main():
    t1 = asyncio.create_task(task1())
    t2 = asyncio.create_task(task2())

    print("Both tasks created")

    # await t1
    # await t2

asyncio.run(main())
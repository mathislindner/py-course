import asyncio

async def count_down(name: str, duration: int):
    for i in range(duration):
        print("Countdown {}: {} s".format(name, duration-i))
        await asyncio.sleep(1)
    print("Countdown {} elapsed!".format(name))

async def main():
    task_1 = asyncio.create_task(count_down(name ="time",duration=5))
    await task_1

asyncio.run(main())
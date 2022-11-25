import asyncio
import aioredis

async def main():
    redis = aioredis.from_url(
        'redis://' + '127.0.0.1')
    await redis.set('foo', 'bar')
    val = await redis.get('foo')
    print(val)

    await redis.close()

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

import asyncpg
import asyncio

async def test_connection():
    try:
        conn = await asyncpg.connect(user='postgres', password='start',
                                     database='image_processing', host='localhost')
        print("Connection successful!")
        await conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

asyncio.run(test_connection())

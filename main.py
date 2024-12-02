from Backend.api_manager import APIManager
import asyncio

async def main():
    api_manager = APIManager()
    await api_manager.initialize()

    # ... Initialize your strategies and subscribe to symbols ...

    # Keep the program running
    await asyncio.Event().wait()

if __name__ == '__main__':
    asyncio.run(main())
from Backend.api_manager import APIManager
import os
import time
import asyncio



async def main():
    api = APIManager()
    api.market_order("AAPL", 1, "buy")


if __name__ == '__main__':
    asyncio.run(main())

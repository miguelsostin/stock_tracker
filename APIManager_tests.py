from Backend.api_manager import APIManager
import os
import time
import asyncio
from alpaca.trading import LimitOrderRequest, OrderSide, OrderType, TimeInForce


async def main():
    api = APIManager()
    print(api.get_net_portfolio_balance())
    print(api.get_day_portfolio_change())
    print(api.get_all_positions())
    data_req = LimitOrderRequest(symbol = 'AAPL',qty = 1, side = OrderSide.BUY, time_in_force = TimeInForce.DAY, limit_price = 100)
    api.clientP.submit_order(data_req)


if __name__ == '__main__':
    asyncio.run(main())

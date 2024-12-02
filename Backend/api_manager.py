from dotenv import load_dotenv
import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetAssetsRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from Backend.database import DatabaseManager
import asyncio
import threading
from alpaca.trading.stream import TradingStream
from alpaca.data.live import StockDataStream
from collections import defaultdict


class APIManager:
    def __init__(self):
        ### Initialize API KEYS from OS
        load_dotenv()

        api_key = os.getenv('API_KEY')
        secret_key = os.getenv('SECRET_KEY')
        paper_key = os.getenv('PAPER_KEY')
        paper_secret_key = os.getenv('PAPER_SECRET_KEY')

        self.api_key = api_key
        self.secret_key = secret_key
        self.paper_key = paper_key
        self.secret_paper_key = paper_secret_key

        ### Initialize Clients
        self.clientP = TradingClient(self.paper_key, self.secret_paper_key, paper=True)
        self.clientT = TradingClient(self.api_key, self.secret_key, paper=False)

        self.account = self.clientP.get_account()

        ### Initialize Order Update Dictionary for Data Storing in DB.
        self.symbol_callbacks = defaultdict(list)
        self.db = DatabaseManager()



    ### Make a market order
    def market_order(self, symbol, qty, side: str, strategy_id=None, time_in_force=TimeInForce.DAY, paper=True):
        """
        Places a market order asynchronously.
        """
        market_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
            time_in_force=time_in_force
        )
        try:
            if paper:
                order = self.clientP.submit_order(order_data=market_order_data)
            else:
                order = self.clientT.submit_order(order_data=market_order_data)
        except Exception as e:
            print(f"Error placing order: {e}")
            return None
        print()

        self.db.insert_order(
            order_id=str(order.id),
            symbol=symbol,
            quantity=qty,
            side=side,
            status=str(order.status),
            strategy_id=strategy_id,
            opened_at=order.submitted_at.isoformat()
        )
        return order
















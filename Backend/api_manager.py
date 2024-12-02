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






load_dotenv()

api_key = os.getenv('API_KEY')
secret_key = os.getenv('SECRET_KEY')
paper_key = os.getenv('PAPER_KEY')
paper_secret_key = os.getenv('PAPER_SECRET_KEY')

class APIManager:
    def __init__(self):
        ### Initialize API KEYS from OS
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper_key = paper_key
        self.secret_paper_key = paper_secret_key

        ### Initialize Clients
        self.clientP = TradingClient(self.paper_key, self.secret_paper_key, paper=True)
        self.clientT = TradingClient(self.api_key, self.secret_key, paper=False)
        self.account = None

        ### Initialize the Streams for order update Collection and Data Stream
        self.streamP = TradingStream(self.paper_key, self.secret_paper_key, paper=True)
        self.data_stream = StockDataStream(self.paper_key, self.secret_paper_key)

        ### Initialize Order Update Dictionary for Data Storing in DB.
        self.order_updates = {}
        self.symbol_callbacks = defaultdict(list)
        self.db = DatabaseManager()


    ### Initialize account asynchronously
    async def initialize_account(self):
        self.account = await self.clientP.get_account()

    async def initialize(self):
        await self.db.connect()
        await self.db.create_tables()
        ##await self.initialize_account()


    ### Make a market order asynchronously
    async def market_order(self, symbol, qty, side: str, strategy_id=None, time_in_force=TimeInForce.DAY, paper=True):
        """
        Places a market order asynchronously.
        """
        market_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
            time_in_force=time_in_force
        )
        if strategy_id:
            market_order_data.client_order_id = strategy_id

        try:
            # Submit the order asynchronously
            if paper:
                order = await self.clientP.submit_order(order_data=market_order_data)
            else:
                order = await self.clientT.submit_order(order_data=market_order_data)
        except Exception as e:
            print(f"Error placing order: {e}")
            return None

        # Insert the order into the database asynchronously
        await self.db.insert_order_async(
            order_id=order.id,
            symbol=symbol,
            quantity=qty,
            side=side,
            status=order.status,
            strategy_id=strategy_id,
            opened_at=order.submitted_at
        )
        return order


    async def start_stream(self):
        self.streamP.subscribe_trade_updates(self.on_trade_update)
        await self.streamP.run()


    async def on_trade_update(self, data):
        # Handle incoming trade updates
        event = data.event
        order_id = data.order['id']


        print(f"Update for order {order_id}: Event: {event}")
        try:
            # Retrieve the order asynchronously
            order = await self.clientP.get_order_by_id(order_id)
            if order.status == 'filled':
                # Retrieve the position asynchronously
                position = await self.clientP.get_open_position(order.symbol)
                await self.db.update_active_position_async(position=position, symbol=order.symbol)

            # Update the order in the database asynchronously
            await self.db.update_order_async(
                order_id=order_id,
                status=order.status,
                avg_price=order.filled_avg_price
            )
        except Exception as e:
            print(f"Error updating order: {e}")


    async def start_data_stream(self):
        # Start the data stream
        await self.data_stream.run()


    async def subscribe_to_symbol(self, symbol, callback):
        # Add the callback to the list for the symbol
        self.symbol_callbacks[symbol].append(callback)

        # Subscribe to the symbol if not already subscribed
        if len(self.symbol_callbacks[symbol]) == 1:
            await self.data_stream.subscribe_quotes(self._handle_quote, symbol)

    async def unsubscribe_from_symbol(self, symbol, callback):
        # Remove the callback from the list
        if callback in self.symbol_callbacks[symbol]:
            self.symbol_callbacks[symbol].remove(callback)

        # Unsubscribe from the symbol if no more callbacks
        if not self.symbol_callbacks[symbol]:
            await self.data_stream.unsubscribe_quotes(symbol)
            del self.symbol_callbacks[symbol]



    async def _handle_quote(self, data):
        symbol = data.symbol
        # Dispatch the data to all registered callbacks for the symbol
        for callback in self.symbol_callbacks.get(symbol, []):
            await callback(data)











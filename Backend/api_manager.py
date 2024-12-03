from dotenv import load_dotenv
import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetAssetsRequest,ClosePositionRequest, GetPortfolioHistoryRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from Backend.database import DatabaseManager
from alpaca.common.enums import BaseURL
from typing import Optional, List, Union
from alpaca.trading.models import PortfolioHistory
from alpaca.common import RawData


class TradingClientPortfolioAble(TradingClient):
    def __init__(
            self,
            api_key: Optional[str] = None,
            secret_key: Optional[str] = None,
            paper: bool = True,

    ) -> None:
        super().__init__(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper
        )

    def get_portfolio_history(
            self, filter: Optional[GetPortfolioHistoryRequest] = None
    ) -> Union[PortfolioHistory, RawData]:
        """
        Gets the portfolio history statistics.

        Args:
            filter (Optional[GetPortfolioHistoryRequest]): The parameters to filter the history with.

        Returns:
            PortfolioHistory: The portfolio history statistics for the account.
        """
        # checking to see if we specified at least one param
        params = filter.to_request_fields() if filter else {}

        response = self.get("/account/portfolio/history", params)

        if self._use_raw_data:
            return response

        return PortfolioHistory(**response)

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

        self.account = None

        ### Initialize Order Update Dictionary for Data Storing in DB.
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
            time_in_force=time_in_force,
            extended_hours = True
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

    def get_account(self):
        """
        Get the account information
        """
        self.account = self.clientP.get_account()
        return self.account

    def get_net_portfolio_balance(self):
        """
        Get the net portfolio balance
        """
        try:
            if self.account is None:
                self.get_account()
            return float(self.account.equity)
        except Exception as e:
            print(f"Error fetching portfolio: {e}")
            return []

    def get_day_portfolio_change(self):
        """
        Get the daily change in the portfolio
        """
        try:
            if self.account is None:
                self.get_account()
            change_today = float(self.account.equity) - float(self.account.last_equity)
            percent_change = (change_today / float(self.account.last_equity)) * 100
            return change_today, percent_change
        except Exception as e:
            print(f"Error fetching portfolio: {e}")
            return []

    def get_portfolio_history(self, start_date = None, end_date= None, timeframe='1D'):
        """
        Get the portfolio history
        """
        try:
            if self.account is None:
                self.get_account()
            portfolio_request = GetPortfolioHistoryRequest(
                period = start_date,
                timeframe = timeframe,
                date_end = end_date
            )
            portfolio_history = TradingClientPortfolioAble(self.paper_key, self.secret_paper_key, paper=True).get_portfolio_history(portfolio_request)
            return portfolio_history
        except Exception as e:
            print(f"Error fetching portfolio history: {e}")

    def get_all_positions(self):
        """
        Get all positions
        """
        try:
            return self.clientP.get_all_positions()
        except Exception as e:
            print(f"Error fetching positions: {e}")

    def get_recent_trades(self):
        """
        Get recent trades
        """

        req = GetOrdersRequest(limit = 10, side = OrderSide.BUY)

        try:
            return self.clientP.get_orders(req)
        except Exception as e:
            print(f"Error fetching trades: {e}")

api = APIManager()
hist = api.get_portfolio_history()
print(hist)














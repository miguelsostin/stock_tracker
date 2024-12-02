from abc import ABC, abstractmethod
from Backend.api_manager import APIManager
from Backend.database import DatabaseManager
import pandas as pd
import numpy as np


class Strategy(ABC):

    def __init__(self, api_manager: APIManager, db_manager: DatabaseManager, symbol: str, strategy_id: str):
        self.api_manager = api_manager
        self.db_manager = db_manager
        self.symbol = symbol
        self.strategy_id = strategy_id

    @abstractmethod
    async def handle_quote(self, data):
        """Handle incoming quote data."""
        pass

    async def start(self):
        """Start the strategy by subscribing to data."""
        await self.api_manager.subscribe_to_symbol(self.symbol, self.handle_quote)

    @abstractmethod
    def analyze(self):
        """Analyze market data and decide whether to buy, sell, or hold."""
        pass

    @abstractmethod
    def execute(self):
        """Execute the trading decision."""
        pass

    def run(self):
        """Run the strategy by analyzing data and executing trades."""
        self.analyze()
        self.execute()

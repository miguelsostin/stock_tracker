import matplotlib
matplotlib.use('Agg')
import datetime
import backtrader as bt
import pandas as pd
import yfinance as yf
import os

class TestStrategy1(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function for this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

class TestStrategy2(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        if self.dataclose[0] < self.dataclose[-1]:
            # current close less than previous close

            if self.dataclose[-1] < self.dataclose[-2]:
                # previous close less than the previous close

                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.buy()

class TestStrategy3(bt.Strategy):

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders
        self.order = None

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log('BUY EXECUTED, %.2f' % order.executed.price)
            elif order.issell():
                self.log('SELL EXECUTED, %.2f' % order.executed.price)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] < self.dataclose[-1]:
                    # current close less than previous close

                    if self.dataclose[-1] < self.dataclose[-2]:
                        # previous close less than the previous close

                        # BUY, BUY, BUY!!! (with default parameters)
                        self.log('BUY CREATE, %.2f' % self.dataclose[0])

                        # Keep track of the created order to avoid a 2nd order
                        self.order = self.buy()

        else:

            # Already in the market ... we might sell
            if len(self) >= (self.bar_executed + 5):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.sell()

class MovingAverageCrossoverStrategy(bt.Strategy):
    params = (
        ('short_period', 50),    # Default short moving average period
        ('long_period', 200),    # Default long moving average period
    )

    def __init__(self):
        # Moving averages
        self.num_trades = 0
        self.short_ma = bt.indicators.MovingAverageSimple(
            self.datas[0].close, period=self.params.short_period)
        self.long_ma = bt.indicators.MovingAverageSimple(
            self.datas[0].close, period=self.params.long_period)

        self.crossover = bt.indicators.CrossOver(self.short_ma, self.long_ma, plot = False)

        self.order = None  # To keep track of pending orders

    def log(self, txt, dt=None):
        ''' Logging function for the strategy '''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
                self.num_trades += 1
                self.log(f'Number of trades: {self.num_trades}')

            self.bar_executed = len(self)

        # Handle rejected orders
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Reset order
        self.order = None

    def next(self):
        # Check for open orders
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # A buy signal when the short MA crosses above the long MA
            if self.crossover > 0:
                self.log(f'BUY CREATE, Price: {self.datas[0].close[0]:.2f}')
                self.order = self.buy()
        else:
            # A sell signal when the short MA crosses below the long MA
            if self.crossover < 0:
                self.log(f'SELL CREATE, Price: {self.datas[0].close[0]:.2f}')
                self.order = self.sell()

class RsiStrategy(bt.Strategy):
    params = (
        ('rsi_period', 14),  # RSI calculation period
        ('rsi_upper', 70),  # Overbought threshold
        ('rsi_lower', 30),  # Oversold threshold
    )

    def __init__(self):
        self.num_trades = 0
        self.rsi = bt.indicators.RSI(
            self.datas[0].close, period=self.params.rsi_period)
        self.order = None  # To keep track of pending orders

    def log(self, txt, dt=None):
        ''' Logging function for the strategy '''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
                self.num_trades += 1
                self.log(f'Number of trades: {self.num_trades}')

            self.bar_executed = len(self)

        # Handle rejected orders
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Reset order
        self.order = None

    def next(self):
        # Check for open orders
        if self.order:
            return

        # Check if we are in the market
        if not self.position:
            # Buy when RSI is below the lower threshold
            if self.rsi < self.params.rsi_lower:
                self.log(f'BUY CREATE, Price: {self.datas[0].close[0]:.2f}')
                self.order = self.buy()
        else:
            # Sell when RSI is above the upper threshold
            if self.rsi > self.params.rsi_upper:
                self.log(f'SELL CREATE, Price: {self.datas[0].close[0]:.2f}')
                self.order = self.sell()

class BollingerBandsStrategy(bt.Strategy):
    params = (
        ('period', 20),
        ('devfactor', 2),
    )

    def __init__(self):
        self.num_trades = 0
        self.bb = bt.indicators.BollingerBands(
            self.datas[0], period=self.params.period, devfactor=self.params.devfactor)
        self.order = None

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.datas[0].close < self.bb.lines.bot:
                self.order = self.buy()
        else:
            if self.datas[0].close > self.bb.lines.top:
                self.order = self.sell()
                self.num_trades += 1
                self.log(f'Number of trades: {self.num_trades}')

    def notify_order(self, order):
        # Check if an order has been completed
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')

            self.bar_executed = len(self)

        # Handle rejected orders
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Reset order
        self.order = None

    def log(self, txt, dt=None):
        ''' Logging function for the strategy '''
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

class MACDStrategy(bt.Strategy):
    params = (
        ('fast_period', 12),
        ('slow_period', 26),
        ('signal_period', 9),
    )

    def __init__(self):
        self.num_trades = 0
        self.macd = bt.indicators.MACD(self.datas[0].close, period_me1 = self.params.fast_period, period_me2 = self.params.slow_period, period_signal = self.params.signal_period)
        self.order = None

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
            else:
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
                self.num_trades += 1
                self.log(f'Number of trades: {self.num_trades}')
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        self.order = None

    def next(self):
        if self.order:
            return

        # Simple logic: if MACD line > Signal line => buy, else sell
        if not self.position:
            if self.macd.macd[0] > self.macd.signal[0]:
                self.log(f'BUY CREATE, Price: {self.datas[0].close[0]:.2f}')
                self.order = self.buy()
        else:
            if self.macd.macd[0] < self.macd.signal[0]:
                self.log(f'SELL CREATE, Price: {self.datas[0].close[0]:.2f}')
                self.order = self.sell()

class MeanReversionStrategy(bt.Strategy):
    params = (
        ('lookback_period', 20),
        ('threshold', 2.0),
    )

    def __init__(self):
        self.num_trades = 0
        self.order = None
        self.mavg = bt.indicators.SimpleMovingAverage(self.datas[0].close, period=self.params.lookback_period)
        self.stddev = bt.indicators.StandardDeviation(self.datas[0].close, period=self.params.lookback_period)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
            else:
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
                self.num_trades += 1
                self.log(f'Number of trades: {self.num_trades}')
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        self.order = None

    def next(self):
        if self.order:
            return

        price = self.datas[0].close[0]
        upper = self.mavg[0] + self.params.threshold * self.stddev[0]
        lower = self.mavg[0] - self.params.threshold * self.stddev[0]

        if not self.position:
            if price < lower:
                self.log(f'BUY CREATE, Price: {price:.2f}')
                self.order = self.buy()
        else:
            if price > upper:
                self.log(f'SELL CREATE, Price: {price:.2f}')
                self.order = self.sell()

class BreakoutStrategy(bt.Strategy):
    params = (
        ('lookback_period', 50),
        ('breakout_factor', 1.5),
    )

    def __init__(self):
        self.num_trades = 0
        self.order = None
        self.highest = bt.indicators.Highest(self.datas[0].high, period=self.params.lookback_period)
        self.lowest = bt.indicators.Lowest(self.datas[0].low, period=self.params.lookback_period)

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)
        print(f'{dt.isoformat()}, {txt}')

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}')
            else:
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}')
                self.num_trades += 1
                self.log(f'Number of trades: {self.num_trades}')
            self.bar_executed = len(self)
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')
        self.order = None

    def next(self):
        if self.order:
            return

        price = self.datas[0].close[0]
        hh = self.highest[-1]
        ll = self.lowest[-1]

        self.log(
            f"Price: {price:.2f}, HH: {hh:.2f}, LL: {ll:.2f}, Conditions: Buy if price > {hh * self.params.breakout_factor}, Sell if price < {ll / self.params.breakout_factor}, {'BUY' if price > hh * self.params.breakout_factor else ''}")

        if not self.position:
            if price > hh * self.params.breakout_factor:
                self.log(f'BUY CREATE, Price: {price:.2f}')
                self.order = self.buy()
        else:
            if price < ll / self.params.breakout_factor:
                self.log(f'SELL CREATE, Price: {price:.2f}')
                self.order = self.sell()





import backtrader as bt
import pandas as pd
import yfinance as yf
import numpy as np

cerebro = bt.Cerebro()
df = yf.download('AAPL', start='2010-01-01', end = '2020-01-01')


df.columns = df.columns.get_level_values(0)

feed = bt.feeds.PandasData(dataname=df)
cerebro.adddata(feed)
cerebro.run()
cerebro.plot()



from alpaca.data import StockBarsRequest
from alpaca.data.historical import StockHistoricalDataClient
from API_Keys import ALPACA_KEYS

keys = ALPACA_KEYS()


client = StockHistoricalDataClient(api_key = keys.API_KEY, secret_key = keys.SECRET_KEY)

from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

request_params = StockBarsRequest(
  symbol_or_symbols=["PLTR"],
  timeframe=TimeFrame.Hour,
  start="2022-09-01",
  end="2022-09-07"
)
btc_bars = client.get_stock_bars(request_params)

dat = btc_bars.df

print(dat['high'])
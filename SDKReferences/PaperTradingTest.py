from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass
import json
from API_Keys import ALPACA_KEYS


keys = ALPACA_KEYS()
trading_client = TradingClient(api_key = keys.PAPER_KEY, secret_key = keys.PAPER_SECRET_KEY)

# Get our account information.
account = trading_client.get_account()


#Tradable US EQUITIES List
search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)

assets = trading_client.get_all_assets(search_params)

# Search for specific assets

specific_asset = trading_client.get_asset('NVDA')

print(specific_asset)

if specific_asset.tradable:
    print('We can trade NVDA.')
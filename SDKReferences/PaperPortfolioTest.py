from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from API_Keys import ALPACA_KEYS


keys = ALPACA_KEYS()
trading_client = TradingClient(api_key = keys.PAPER_KEY, secret_key = keys.PAPER_SECRET_KEY)

# Get our account information.
account = trading_client.get_account()

# Check if our account is restricted from trading.
if account.trading_blocked:
    print('Account is currently restricted from trading.')

# Check how much money we can use to open new positions.
print('${} is available as buying power.'.format(account.buying_power))

balance_change = float(account.equity) - float(account.last_equity)
print(f'Today\'s portfolio balance change: ${balance_change}')
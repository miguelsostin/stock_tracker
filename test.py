import os
import time
from dotenv import load_dotenv
from Backend.WebSocketClient import StockDataWebSocketClient

def trade_handler(message):
    print("Received trade data:")
    print(message)

def quote_handler(message):
    print("Received quote data:")
    print(message)
def bar_handler(message):
    print("Received bar data:")
    print(message)

def main():
    load_dotenv()
    data_key = os.getenv('PAPER_KEY')  # Use your data API key
    data_secret_key = os.getenv('PAPER_SECRET_KEY')
    base_url = "wss://stream.data.alpaca.markets/v2/test"

    stock_ws = StockDataWebSocketClient(data_key, data_secret_key, base_url)

    # Subscribe to trades and quotes for AAPL
    channels = {
        "trades": ["FAKEPACA"],
        "quotes": ["FAKEPACA"],
        "bars": ["FAKEPACA"]  # Optional
    }
    stock_ws.subscribe(channels)

    # Register callbacks
    stock_ws.register_callback('t', trade_handler)  # 't' for trade messages
    stock_ws.register_callback('q', quote_handler)  # 'q' for quote messages
    stock_ws.register_callback('q', bar_handler)  # 'q' for quote messages

    stock_ws.connect()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Closing Stock Data WebSocket connection.")
        stock_ws.close()

if __name__ == "__main__":
    main()
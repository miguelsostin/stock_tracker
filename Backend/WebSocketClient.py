
import os
import json
import threading
import websocket
from dotenv import load_dotenv

class StockDataWebSocketClient:
    def __init__(self, api_key, secret_key, base_url):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url
        self.ws = None
        self.connected = False
        self.callbacks = {}  # Map message types to callbacks
        self.channels = {}   # Subscription channels
        self.thread = None

    def connect(self):
        self.ws = websocket.WebSocketApp(
            self.base_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        # Run the WebSocket in a separate thread
        self.thread = threading.Thread(target=self.ws.run_forever, daemon=True)
        self.thread.start()

    def on_open(self, ws):
        print("Stock Data WebSocket connection opened.")
        # Authenticate
        auth_data = {
            "action": "auth",
            "key": self.api_key,
            "secret": self.secret_key
        }
        ws.send(json.dumps(auth_data))

    def on_message(self, ws, message):
        message_data = json.loads(message)
        self.handle_message(message_data)

    def on_error(self, ws, error):
        print(f"Stock Data WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"Stock Data WebSocket connection closed: {close_status_code} - {close_msg}")
        self.connected = False
        # Reconnect logic if desired

    def handle_message(self, message):
        if isinstance(message, dict):
            # Process a single message
            message_type = message.get('T')
            if message_type == 'success' and message.get('msg') == 'authenticated':
                print("Stock Data WebSocket authenticated.")
                self.connected = True
                # Subscribe to streams
                self.subscribe_to_streams()
            elif message_type == 'subscription':
                print(f"Subscribed to streams: {message}")
            else:
                if message_type in self.callbacks:
                    for callback in self.callbacks[message_type]:
                        callback(message)
                else:
                    print(f"Unhandled message type: {message}")

        elif isinstance(message, list):
            # Process each message in the list
            for msg in message:
                self.handle_message(msg)
        else:
            print(f"Unexpected message format: {message}")

    def subscribe(self, channels):
        self.channels = channels
        if self.connected:
            self.subscribe_to_streams()

    def subscribe_to_streams(self):
        subscribe_message = {
            "action": "subscribe",
        }
        subscribe_message.update(self.channels)
        self.ws.send(json.dumps(subscribe_message))
        print(f"Subscribed to streams: {self.channels}")

    def register_callback(self, message_type, callback):
        if message_type not in self.callbacks:
            self.callbacks[message_type] = []
        self.callbacks[message_type].append(callback)

    def close(self):
        self.ws.close()
        if self.thread is not None:
            self.thread.join()
# core/stream.py

import json
import threading
import websocket

# Shared price cache — all monitors read from here
price_cache = {}


def start_stream(symbols):
    """Start a WebSocket stream for multiple symbols"""
    streams = "/".join([f"{s.lower()}@trade" for s in symbols])
    url = f"wss://stream.binance.com:9443/stream?streams={streams}"

    def on_message(ws, message):
        data = json.loads(message)
        if "data" in data:
            symbol = data["data"]["s"]  # e.g. NEARUSDT
            price = float(data["data"]["p"])  # trade price
            price_cache[symbol] = price

    def on_error(ws, error):
        print(f"Stream error: {error}")

    def on_close(ws, close_status_code, close_msg):
        print("Stream closed, reconnecting...")
        threading.Timer(5, lambda: start_stream(symbols)).start()

    def on_open(ws):
        print(f"✅ Stream connected for: {symbols}")

    ws = websocket.WebSocketApp(
        url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
        on_open=on_open,
    )
    thread = threading.Thread(target=ws.run_forever)
    thread.daemon = True
    thread.start()


def get_cached_price(symbol):
    """Get price from cache, fallback to None if not available"""
    return price_cache.get(symbol)
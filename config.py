# config.py
import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
API_KEY = os.environ.get("BINANCE_API_KEY")
API_SECRET = os.environ.get("BINANCE_API_SECRET")

settings = {
    "min_profit": 1.0,
    "trail_amount": 0.50,
    "hard_stop_loss": -1.0,
    "daily_loss_limit": -10.0,
}
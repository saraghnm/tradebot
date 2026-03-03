# config.example.py
# Create a file named config.py and copy this content to it, then fill in your credentials

# Telegram
TELEGRAM_TOKEN = "your_telegram_bot_token_here"
TELEGRAM_CHAT_ID = "your_telegram_chat_id_here"

# Binance
API_KEY = "your_binance_api_key_here"
API_SECRET = "your_binance_api_secret_here"

# Anthropic (Claude AI) — get from https://platform.claude.com
ANTHROPIC_API_KEY = "your_anthropic_api_key_here"

settings = {
    "min_profit": 1.0,        # Minimum profit ($) to activate trailing stop
    "trail_percent": 5.0,     # Trailing stop percentage (5% below highest price)
    "hard_stop_loss": -1.0,   # Maximum loss per trade ($)
    "daily_loss_limit": -10.0, # Maximum daily loss ($)
}
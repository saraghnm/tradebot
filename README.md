# 🤖 zTrading Bot

A Telegram-controlled crypto trading bot built with Python and Binance API. Supports real-time price monitoring, trailing stop-loss, custom stop prices, price alerts, and full trade management via Telegram commands.

---

## ✨ Features

- **Trailing Stop-Loss** — automatically follows price up and sells when it drops
- **Custom Stop Price** — set exact price-based stop loss per trade
- **Price Alerts** — auto-buy when a coin hits your target price
- **State Persistence** — remembers active trades and alerts after restart
- **Multi-Trade Support** — monitor multiple coins simultaneously
- **Daily Loss Limit** — auto-stop trading if daily loss exceeds threshold
- **Smart Error Handling** — silent retries with single notification on failure
- **Telegram Control** — full bot management from your phone

---

## 📁 Project Structure

```
tradebot/
├── bot.py              # Main entry point, runs the bot
├── commands.py         # Telegram command handling
├── trader.py           # Binance trading logic
├── notifier.py         # Telegram notifications
├── state.py            # State persistence (trades, alerts)
├── config.py           # Credentials and settings (not committed)
├── config.example.py   # Template for config.py
├── requirements.txt    # Python dependencies
└── .gitignore
```

---

## 🚀 Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/tradebot.git
cd tradebot
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure credentials
```bash
cp config.example.py config.py
```
Fill in your Binance API key and Telegram bot token in `config.py`.

### 4. Run the bot
```bash
python bot.py
```

---

## 📱 Telegram Commands

### 🪙 Trading
| Command | Description |
|--------|-------------|
| `buy COIN 10` | Buy $10 of a coin |
| `buy COIN 10 0.085` | Buy with custom stop loss price |
| `sell COIN` | Force sell a coin |
| `setstop COIN 0.085` | Update stop loss for active trade |
| `alert COIN 1.70 10 1.60` | Auto-buy when price hits target |
| `alerts` | View all active alerts |
| `cancelalert COIN` | Cancel a price alert |

### 📊 Monitoring
| Command | Description |
|--------|-------------|
| `price COIN` | Get current price |
| `status` | View active trades and P/L |
| `summary` | Daily trade summary |
| `balance` | Check wallet balances |
| `orders COIN` | Last 5 orders |

### ⚙️ Settings
| Command | Description |
|--------|-------------|
| `set min_profit 1.5` | Minimum profit to activate trailing stop |
| `set trail_amount 0.50` | Trailing stop distance |
| `set hard_stop_loss -1.0` | Maximum loss per trade |
| `set daily_loss_limit -10.0` | Maximum daily loss |

---

## ⚙️ How It Works

1. You send `buy DOGE 10 0.085` via Telegram
2. Bot places a market buy order on Binance
3. Bot monitors the price every 2 seconds
4. When profit reaches `min_profit` → trailing stop activates
5. Trailing stop follows price up automatically
6. When price drops to stop level → bot sells and notifies you

---

## 🛡️ Risk Management

- **Hard stop-loss** — sells immediately if loss exceeds threshold
- **Daily loss limit** — stops all trading for the day if limit hit
- **Custom stop price** — price-based stop loss per trade
- **No martingale** — flat position sizing only

---

## 🧰 Tech Stack

- **Python 3.10+**
- **python-binance** — Binance API wrapper
- **requests** — Telegram API integration
- **threading** — concurrent trade monitoring

---

## 🔜 Roadmap

- [ ] VPS hosting for 24/7 operation
- [ ] Forex bot with MetaTrader 5
- [ ] Web dashboard (Next.js + Chart.js)
- [ ] AI/ML signal prediction

---

## ⚠️ Disclaimer

This bot is for educational purposes. Crypto trading involves significant financial risk. Only trade with money you can afford to lose.
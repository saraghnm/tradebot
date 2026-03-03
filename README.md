# 🤖 zTrading Bot

A Telegram-controlled crypto trading bot built with Python and Binance API. Supports real-time WebSocket price streaming, AI-powered multi-timeframe analysis, trailing stop-loss, take profit levels, price alerts, coin tracking, trade history, and full trade management via Telegram.

---

## ✨ Features

- **WebSocket Streaming** — real-time price feeds from Binance for faster stop-loss triggers
- **AI Market Analysis** — multi-timeframe analysis (1H, 4H, 1D) powered by Claude AI
- **Take Profit Levels** — sell 50% at TP1, activate trailing stop at TP2
- **Break Even Stop** — automatically moves stop to entry price after TP1 hits
- **Trailing Stop-Loss** — percentage-based, follows price up and sells on reversal
- **Auto Re-entry** — AI analyzes trend after trailing stop, sets re-entry alert if safe
- **Price Alerts** — auto-buy when a coin hits your target price
- **Coin Tracker** — monitor any coin and get notified on big % moves
- **Trade History** — log of all closed trades with entry/exit/profit
- **Trading Stats** — win rate, total P/L, best and worst trades
- **Daily Summary** — automatic midnight report and P/L reset
- **State Persistence** — remembers trades and alerts after restart
- **Multi-Trade Support** — monitor multiple coins simultaneously
- **Daily Loss Limit** — auto-stop trading if daily loss exceeds threshold
- **Smart Error Handling** — clean error messages, silent retries on connection issues
- **Telegram Control** — full bot management from your phone

---

## 📁 Project Structure

```
tradebot/
├── bot.py                  # Main entry point
├── commands.py             # Telegram command handling
├── config.py               # Credentials and settings (not committed)
├── config.example.py       # Template for config.py
├── requirements.txt        # Python dependencies
├── .gitignore
└── core/
    ├── trader.py           # Binance trading logic
    ├── analyzer.py         # AI multi-timeframe analysis
    ├── notifier.py         # Telegram notifications
    ├── state.py            # State persistence
    ├── history.py          # Trade history and stats
    ├── scheduler.py        # Midnight reset and daily summary
    └── stream.py           # WebSocket price streaming
```

---

## 🚀 Setup

### 1. Clone the repo
```bash
git clone https://github.com/saraghnm/tradebot.git
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
Fill in your Binance API key, Telegram bot token, and Anthropic API key in `config.py`.

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
| `buy COIN 10 0.085` | Buy with stop loss |
| `buy COIN 10 0.085 1.30 1.50` | Buy with stop loss + take profits |
| `sell COIN` | Force sell a coin |
| `setstop COIN 0.085` | Update stop loss for active trade |

### 🎯 Alerts
| Command | Description |
|--------|-------------|
| `alert COIN 1.70 10 1.60` | Auto-buy when price hits target |
| `alerts` | View all active alerts |
| `cancelalert COIN` | Cancel a price alert |

### 👀 Tracking
| Command | Description |
|--------|-------------|
| `track COIN` | Alert on 5% price moves |
| `track COIN 3` | Alert on 3% price moves |
| `untrack COIN` | Stop tracking a coin |
| `trackers` | View all tracked coins |

### 📊 Monitoring
| Command | Description |
|--------|-------------|
| `price COIN` | Get current price |
| `status` | View active trades and P/L |
| `summary` | Daily trade summary |
| `balance` | Check wallet balances |
| `orders COIN` | Last 5 orders |
| `analyze COIN` | AI multi-timeframe analysis |
| `history` | Last 10 closed trades |
| `stats` | Win rate and total P/L |

### ⚙️ Settings
| Command | Description |
|--------|-------------|
| `set min_profit 1.5` | Minimum profit to activate trailing stop |
| `set trail_percent 5.0` | Trailing stop percentage |
| `set hard_stop_loss -1.0` | Maximum loss per trade |
| `set daily_loss_limit -10.0` | Maximum daily loss |

---

## ⚙️ How It Works

1. You send `buy NEAR 10 1.35 1.50 1.60` via Telegram
2. Bot places a market buy order on Binance
3. Bot monitors price in real-time via WebSocket
4. At **TP1 ($1.50)** → sells 50%, moves stop to break even
5. At **TP2 ($1.60)** → activates trailing stop on remaining 50%
6. Trailing stop follows price up automatically
7. When price drops to stop → bot sells, notifies you, and runs AI analysis for re-entry

---

## 🤖 AI Analysis

The `analyze COIN` command fetches 1H, 4H, and 1D candle data and sends it to Claude AI for analysis:

```
1H Trend: Bearish
4H Trend: Bullish
1D Trend: Bullish
Overall: Bullish
Strength: Moderate
RSI estimate: Overbought
Support: $1.30
Resistance: $1.42
Re-entry safe: No
Suggested re-entry: $1.28
Summary: ...
```

Auto re-entry also uses AI — after a trailing stop triggers, the bot analyzes the trend and only sets a re-entry alert if it's safe.

---

## 🛡️ Risk Management

- **Hard stop-loss** — sells immediately if loss exceeds threshold
- **Daily loss limit** — stops all trading for the day if limit hit
- **Custom stop price** — price-based stop loss per trade
- **Break even stop** — moves stop to entry after first take profit
- **No martingale** — flat position sizing only

---

## 🧰 Tech Stack

- **Python 3.10+**
- **python-binance** — Binance API wrapper
- **websocket-client** — real-time price streaming
- **anthropic** — Claude AI for market analysis
- **requests** — Telegram API integration
- **threading** — concurrent trade monitoring

---

## 🔜 Roadmap

- [ ] VPS hosting for 24/7 operation
- [ ] Partial sell command (`sell COIN 50%`)
- [ ] Web dashboard (Next.js + Chart.js)
- [ ] Forex bot with MetaTrader 5
- [ ] AI/ML signal prediction

---

## ⚠️ Disclaimer

This bot is for educational purposes. Crypto trading involves significant financial risk. Only trade with money you can afford to lose.
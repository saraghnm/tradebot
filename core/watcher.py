# core/watcher.py
#
# Auto-trading watcher — mirrors the Forex bot's scan loop pattern.
# Analyzes 1D (bias) -> 4H (confirmation) -> 1H (entry trigger).
# Fires buy/sell using the existing trader.py functions.

import time
import threading
import pandas as pd
import ta
from binance.client import Client
from config import API_KEY, API_SECRET, settings
from core.notifier import notify
from core.state import save_state, load_state
from core.trader import (
    active_trades,
    buy,
    monitor_trade,
    get_price,
    get_error_message,
)

client = Client(API_KEY, API_SECRET)

# symbol -> thread running for it
active_watchers = {}

# symbol -> watcher config (for persistence)
saved_watchers = {}

# symbol -> cooldown end timestamp (epoch seconds)
watcher_cooldowns = {}

SCAN_INTERVAL = 60 * 15  # scan every 15 minutes


# -- Candle fetcher -----------------------------------------------------------

def get_candles(symbol, interval, limit=100):
    raw = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(raw, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_vol", "trades", "taker_base", "taker_quote", "ignore"
    ])
    df["close"] = df["close"].astype(float)
    df["high"]  = df["high"].astype(float)
    df["low"]   = df["low"].astype(float)
    return df


# -- Per-timeframe signal -----------------------------------------------------

def get_timeframe_bias(symbol, interval, limit=100):
    df = get_candles(symbol, interval, limit)
    if len(df) < 21:
        return "NEUTRAL"
    df["ema9"]  = ta.trend.ema_indicator(df["close"], window=9)
    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    curr = df.iloc[-1]
    if curr["ema9"] > curr["ema20"]:
        return "BULLISH"
    elif curr["ema9"] < curr["ema20"]:
        return "BEARISH"
    return "NEUTRAL"


def get_entry_signal(symbol):
    df = get_candles(symbol, Client.KLINE_INTERVAL_1HOUR, 100)
    if len(df) < 21:
        return "NONE", None
    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["rsi"]   = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    df["atr"]   = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
    curr  = df.iloc[-1]
    price = curr["close"]
    ema20 = curr["ema20"]
    rsi   = curr["rsi"]
    atr   = curr["atr"]
    details = {
        "price": round(price, 6),
        "ema20": round(ema20, 6),
        "rsi":   round(rsi, 2),
        "atr":   round(atr, 6),
    }
    near_ema_low  = price <= ema20 * 1.002
    rsi_ok_buy    = rsi < 65
    near_ema_high = price >= ema20 * 0.998
    rsi_ok_sell   = rsi > 65
    if near_ema_low and rsi_ok_buy:
        return "BUY", details
    elif near_ema_high and rsi_ok_sell:
        return "SELL", details
    return "NONE", details


# -- Main scan logic ----------------------------------------------------------

def scan(symbol):
    bias_1d = get_timeframe_bias(symbol, Client.KLINE_INTERVAL_1DAY)
    bias_4h = get_timeframe_bias(symbol, Client.KLINE_INTERVAL_4HOUR)
    if bias_1d != bias_4h or bias_1d == "NEUTRAL":
        return None
    signal, details = get_entry_signal(symbol)
    if signal == "NONE":
        return None
    if signal == "BUY" and bias_1d != "BULLISH":
        return None
    if signal == "SELL" and bias_1d != "BEARISH":
        return None
    return {
        "signal":  signal,
        "bias_1d": bias_1d,
        "bias_4h": bias_4h,
        "details": details,
    }


# -- Watcher loop -------------------------------------------------------------

def watch_loop(symbol, amount, custom_stop=None, take_profit1=None, take_profit2=None):
    import core.trader as _trader
    notify(
        "👁 Watching " + symbol + "\n"
        "Amount: $" + str(amount) + "\n"
        "Scans every 15 min — will auto-buy on signal"
    )

    while symbol in active_watchers:
        try:
            # Skip if already in an active trade
            if symbol in active_trades:
                time.sleep(SCAN_INTERVAL)
                continue

            # Skip if daily loss limit hit
            if _trader.daily_pnl <= settings["daily_loss_limit"]:
                notify("🚫 Daily loss limit hit — " + symbol + " watcher paused for today")
                time.sleep(SCAN_INTERVAL)
                continue

            # Skip if in cooldown after a loss
            cooldown_until = watcher_cooldowns.get(symbol, 0)
            if time.time() < cooldown_until:
                time.sleep(SCAN_INTERVAL)
                continue

            result = scan(symbol)

            if result and result["signal"] == "BUY":
                d   = result["details"]
                atr = d["atr"]

                # ATR-based risk management
                sl  = round(d["price"] - (atr * 1.5), 6)
                tp1 = round(d["price"] + (atr * 2.0), 6)
                tp2 = round(d["price"] + (atr * 3.0), 6)

                notify(
                    "🟢 AUTO SIGNAL: BUY " + symbol + "\n"
                    "──────────────\n"
                    "1D: " + result["bias_1d"] + "  4H: " + result["bias_4h"] + "\n"
                    "Price: $" + str(d["price"]) + "\n"
                    "RSI:   " + str(d["rsi"]) + "\n"
                    "ATR:   " + str(atr) + "\n"
                    "──────────────\n"
                    "Stop:  $" + str(sl) + "\n"
                    "TP1:   $" + str(tp1) + " (sell 50%)\n"
                    "TP2:   $" + str(tp2) + " (trail rest)\n"
                    "──────────────\n"
                    "Placing order for $" + str(amount) + "..."
                )
                quantity, entry_price = buy(symbol, amount)
                thread = threading.Thread(
                    target=monitor_trade,
                    args=(symbol, quantity, entry_price, amount, sl, tp1, tp2)
                )
                thread.daemon = True
                thread.start()

                notify("✅ " + symbol + " bought — watcher will resume after trade closes")
                while symbol in active_trades and symbol in active_watchers:
                    time.sleep(30)

                # Check if trade closed at a loss — apply cooldown
                try:
                    from core.history import get_history
                    recent = get_history(1)
                    if recent and recent[-1]["symbol"] == symbol and recent[-1]["profit"] < 0:
                        cooldown_hours = settings.get("watcher_cooldown_hours", 4)
                        watcher_cooldowns[symbol] = time.time() + (cooldown_hours * 3600)
                        notify(
                            "⏳ " + symbol + " watcher cooling down for " + str(cooldown_hours) + "h\n"
                            "Last trade was a loss — pausing before re-scanning"
                        )
                except Exception:
                    pass

        except Exception as e:
            notify("⚠️ Watcher error " + symbol + ": " + get_error_message(e))
            time.sleep(60)
            continue

        time.sleep(SCAN_INTERVAL)

    notify("🛑 Watcher stopped for " + symbol)


# -- Public API ---------------------------------------------------------------

def get_bias(symbol):
    """Returns formatted bias string for a symbol across all 3 timeframes."""
    try:
        bias_1d = get_timeframe_bias(symbol, Client.KLINE_INTERVAL_1DAY)
        bias_4h = get_timeframe_bias(symbol, Client.KLINE_INTERVAL_4HOUR)
        signal, details = get_entry_signal(symbol)

        e1d = "📈" if bias_1d == "BULLISH" else "📉" if bias_1d == "BEARISH" else "➡️"
        e4h = "📈" if bias_4h == "BULLISH" else "📉" if bias_4h == "BEARISH" else "➡️"
        esig = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "🟡"

        cooldown_until = watcher_cooldowns.get(symbol, 0)
        cooldown_str = ""
        if time.time() < cooldown_until:
            remaining = int((cooldown_until - time.time()) / 60)
            cooldown_str = "\n⏳ Cooldown: " + str(remaining) + "m remaining"

        watching_str = "👁 Watching" if symbol in active_watchers else "Not watching"
        rsi_str = "RSI: " + str(details["rsi"]) if details else ""
        atr_str = "ATR: " + str(details["atr"]) if details else ""

        lines = [
            "📊 " + symbol + " Bias",
            "──────────────",
            e1d + " 1D: " + bias_1d,
            e4h + " 4H: " + bias_4h,
            "──────────────",
            esig + " 1H Signal: " + signal,
            rsi_str,
            atr_str,
            "──────────────",
            watching_str + cooldown_str,
        ]
        return "\n".join(l for l in lines if l)

    except Exception as e:
        return "❌ Bias check failed for " + symbol + ": " + str(e)


def _persist():
    """Save current watcher config to state.json."""
    import core.trader as _trader
    save_state(_trader.active_trades, _trader.daily_pnl, _trader.active_alerts, saved_watchers)


def start_watcher(symbol, amount, custom_stop=None, take_profit1=None, take_profit2=None):
    if symbol in active_watchers:
        return False

    active_watchers[symbol] = True
    saved_watchers[symbol] = {
        "amount":       amount,
        "custom_stop":  custom_stop,
        "take_profit1": take_profit1,
        "take_profit2": take_profit2,
    }
    _persist()

    thread = threading.Thread(
        target=watch_loop,
        args=(symbol, amount, custom_stop, take_profit1, take_profit2)
    )
    thread.daemon = True
    thread.start()
    return True


def stop_watcher(symbol):
    if symbol in active_watchers:
        active_watchers.pop(symbol)
        saved_watchers.pop(symbol, None)
        _persist()
        return True
    return False
# core/watcher.py
#
# Auto-trading watcher — mirrors the Forex bot's scan loop pattern.
# Analyzes 1D (bias) → 4H (confirmation) → 1H (entry trigger).
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
    daily_pnl,
    buy,
    monitor_trade,
    get_price,
    get_error_message,
)

client = Client(API_KEY, API_SECRET)

# symbol → thread running for it
active_watchers = {}

# symbol → watcher config (for persistence)
saved_watchers = {}

SCAN_INTERVAL = 60 * 15  # scan every 15 minutes


# ── Candle fetcher ────────────────────────────────────────────────────────────

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


# ── Per-timeframe signal ──────────────────────────────────────────────────────

def get_timeframe_bias(symbol, interval, limit=100):
    """
    Returns 'BULLISH', 'BEARISH', or 'NEUTRAL' for a given timeframe.
    Uses EMA9 vs EMA20 crossover — same approach as the Forex trend_engine.
    """
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
    """
    Checks 1H candles for an entry trigger.
    Mirrors the Forex entry_scanner: price near EMA20 + RSI confirmation.
    Returns 'BUY', 'SELL', or 'NONE' + details dict.
    """
    df = get_candles(symbol, Client.KLINE_INTERVAL_1HOUR, 100)
    if len(df) < 21:
        return "NONE", None

    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["rsi"]   = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    df["atr"]   = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()

    curr = df.iloc[-1]
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

    # BUY: price pulled back to EMA, RSI not overbought
    near_ema_low  = price <= ema20 * 1.002  # within 0.2% below EMA
    rsi_ok_buy    = rsi < 65

    # SELL/EXIT: price extended above EMA, RSI overbought
    near_ema_high = price >= ema20 * 0.998
    rsi_ok_sell   = rsi > 65

    if near_ema_low and rsi_ok_buy:
        return "BUY", details
    elif near_ema_high and rsi_ok_sell:
        return "SELL", details

    return "NONE", details


# ── Main scan logic ───────────────────────────────────────────────────────────

def scan(symbol, amount, custom_stop=None, take_profit1=None, take_profit2=None):
    """
    Full top-down analysis for one symbol.
    1D bias → 4H confirmation → 1H entry trigger.
    Returns signal dict or None.
    """
    bias_1d = get_timeframe_bias(symbol, Client.KLINE_INTERVAL_1DAY)
    bias_4h = get_timeframe_bias(symbol, Client.KLINE_INTERVAL_4HOUR)

    # Both higher timeframes must agree
    if bias_1d != bias_4h or bias_1d == "NEUTRAL":
        return None

    signal, details = get_entry_signal(symbol)

    # Signal must match the higher-timeframe bias
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


# ── Watcher loop ──────────────────────────────────────────────────────────────

def watch_loop(symbol, amount, custom_stop=None, take_profit1=None, take_profit2=None):
    notify(
        f"👁 Watching {symbol}\n"
        f"Amount: ${amount}\n"
        f"Scans every 15 min — will auto-buy on signal"
    )

    while symbol in active_watchers:
        try:
            # Skip if already in an active trade
            if symbol in active_trades:
                time.sleep(SCAN_INTERVAL)
                continue

            # Skip if daily loss limit hit
            if daily_pnl <= settings["daily_loss_limit"]:
                notify(f"🚫 Daily loss limit hit — {symbol} watcher paused for today")
                time.sleep(SCAN_INTERVAL)
                continue

            result = scan(symbol, amount, custom_stop, take_profit1, take_profit2)

            if result and result["signal"] == "BUY":
                d = result["details"]
                notify(
                    f"🟢 AUTO SIGNAL: BUY {symbol}\n"
                    f"──────────────\n"
                    f"1D: {result['bias_1d']}  4H: {result['bias_4h']}\n"
                    f"Price: ${d['price']:,}\n"
                    f"EMA20: ${d['ema20']:,}\n"
                    f"RSI:   {d['rsi']}\n"
                    f"ATR:   {d['atr']}\n"
                    f"──────────────\n"
                    f"Placing order for ${amount}..."
                )
                quantity, entry_price = buy(symbol, amount)
                thread = threading.Thread(
                    target=monitor_trade,
                    args=(symbol, quantity, entry_price, amount, custom_stop, take_profit1, take_profit2)
                )
                thread.daemon = True
                thread.start()

                # After buying, pause the watcher until trade closes
                notify(f"✅ {symbol} bought — watcher will resume after trade closes")
                while symbol in active_trades and symbol in active_watchers:
                    time.sleep(30)

        except Exception as e:
            notify(f"⚠️ Watcher error {symbol}: {get_error_message(e)}")
            time.sleep(60)
            continue

        time.sleep(SCAN_INTERVAL)

    notify(f"🛑 Watcher stopped for {symbol}")


# ── Public API ────────────────────────────────────────────────────────────────

def _persist():
    """Save current watcher config to state.json."""
    from core.trader import active_trades, daily_pnl, active_alerts
    save_state(active_trades, daily_pnl, active_alerts, saved_watchers)


def start_watcher(symbol, amount, custom_stop=None, take_profit1=None, take_profit2=None):
    if symbol in active_watchers:
        return False  # already running

    active_watchers[symbol] = True
    saved_watchers[symbol] = {
        "amount": amount,
        "custom_stop": custom_stop,
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
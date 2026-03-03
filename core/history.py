# core/history.py

import json
import os
from datetime import datetime

HISTORY_FILE = "history.json"


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []


def save_trade(symbol, entry_price, exit_price, investment, profit, reason):
    history = load_history()
    history.append({
        "symbol": symbol,
        "entry_price": entry_price,
        "exit_price": exit_price,
        "investment": investment,
        "profit": round(profit, 4),
        "reason": reason,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def get_history(limit=10):
    history = load_history()
    return history[-limit:]


def get_stats():
    history = load_history()
    if not history:
        return None
    total = len(history)
    wins = [t for t in history if t["profit"] > 0]
    losses = [t for t in history if t["profit"] <= 0]
    total_profit = sum(t["profit"] for t in history)
    return {
        "total": total,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": (len(wins) / total * 100),
        "total_profit": round(total_profit, 4),
        "best": max(history, key=lambda x: x["profit"]),
        "worst": min(history, key=lambda x: x["profit"]),
    }

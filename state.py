# state.py

import json
import os

STATE_FILE = "state.json"


def save_state(active_trades, daily_pnl, active_alerts={}):
    with open(STATE_FILE, "w") as f:
        json.dump({
            "active_trades": active_trades,
            "daily_pnl": daily_pnl,
            "active_alerts": active_alerts
        }, f)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"active_trades": {}, "daily_pnl": 0.0, "active_alerts": {}}


def clear_state():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
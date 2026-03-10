# core/notifier.py

import requests
import time
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID


def notify(message, retries=3):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for attempt in range(retries):
        try:
            response = requests.post(
                url,
                data={"chat_id": TELEGRAM_CHAT_ID, "text": message},
                timeout=10
            )
            if response.status_code == 200:
                return
            elif response.status_code == 429:
                # Rate limited — wait and retry
                retry_after = response.json().get("parameters", {}).get("retry_after", 5)
                time.sleep(retry_after)
            else:
                time.sleep(2)
        except requests.exceptions.Timeout:
            time.sleep(2)
        except requests.exceptions.ConnectionError:
            time.sleep(5)
        except Exception:
            time.sleep(2)


def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset
    try:
        response = requests.get(url, params=params, timeout=15)
        return response.json()
    except Exception:
        return {"result": []}
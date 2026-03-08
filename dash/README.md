# zTrading Dashboard — Setup Guide

## Folder structure
```
dash/
├── api.py          ← Flask API server (reads state.json + history.json)
└── dashboard/      ← Next.js frontend
```

Place the `dash/` folder inside your bot's root directory:
```
tradebot/
├── bot.py
├── api.py          ← NOT here, see below
├── state.json
├── history.json
└── dash/
    ├── api.py      ← runs from here, reads ../state.json
    └── dashboard/
```

---

## 1. Install API dependencies

```bash
pip install flask flask-cors
```

---

## 2. Run the API server

```bash
# From inside the dash/ folder
cd dash
python api.py
# Runs on http://localhost:5000
```

> **Note:** `api.py` reads `state.json` and `history.json` from the **parent directory** (`../`). Make sure you run it from inside `dash/`.

Update the paths in `api.py` if needed:
```python
STATE_FILE = "../state.json"
HISTORY_FILE = "../history.json"
```

API endpoints:
- `GET /api/health` — status check
- `GET /api/state` — active trades + daily P/L
- `GET /api/history` — last 50 closed trades
- `GET /api/stats` — win rate, total P/L, best/worst trade
- `GET /api/equity` — cumulative P/L over time (equity curve)

---

## 3. Set up the dashboard

```bash
cd dash/dashboard
npm install
```

Create a `.env.local` file inside `dash/dashboard/`:
```
NEXT_PUBLIC_API_URL=http://YOUR_VPS_IP:5000
```

Build and run:
```bash
npm run build
npm start
# Runs on http://YOUR_VPS_IP:3000
```

---

## 4. Run both with PM2 (recommended for VPS)

```bash
npm install -g pm2

# Start the Flask API (from bot root)
cd ~/tradebot/dash
pm2 start "python api.py" --name "trading-api"

# Start the Next.js dashboard
cd ~/tradebot/dash/dashboard
pm2 start "npm start" --name "trading-dashboard"

pm2 save
pm2 startup  # Auto-start on reboot
```

---

## 5. Access the dashboard

Open in browser: `http://YOUR_VPS_IP:3000`

Auto-refreshes every 30 seconds.

---

## Open VPS firewall ports

```bash
sudo ufw allow 5000   # Flask API
sudo ufw allow 3000   # Next.js dashboard
```

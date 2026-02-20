import os
import json
import time
import threading
import requests
import websocket
from flask import Flask

# ================= CONFIG =================

BOT_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

SYMBOL = "BTCUSDT"
THRESHOLD_PERCENT = 0.01
WINDOW_SECONDS = 300

price_history = []
last_alert_time = 0

# ================= TELEGRAM =================

def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("TOKEN or CHAT_ID not set")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}

    try:
        response = requests.post(url, data=data, timeout=10)
        print("Telegram:", response.text)
    except Exception as e:
        print("Telegram error:", e)

# ================= PRICE LOGIC =================

def process_price(price):
    global price_history, last_alert_time

    now = time.time()
    price_history.append((now, price))

    # удаляем старые данные
    price_history[:] = [(t, p) for t, p in price_history if now - t <= WINDOW_SECONDS]

    if len(price_history) < 2:
        return

    old_price = price_history[0][1]
    change = ((price - old_price) / old_price) * 100

    if abs(change) >= THRESHOLD_PERCENT:
        if now - last_alert_time > WINDOW_SECONDS:
            direction = "🟢 PUMP" if change > 0 else "🔴 DUMP"
            msg = f"{direction} {SYMBOL}\nИзменение: {change:.2f}%\nЦена: {price}"
            send_telegram(msg)
            last_alert_time = now

# ================= WEBSOCKET =================

def on_message(ws, message):
    try:
        data = json.loads(message)

        if "data" in data and isinstance(data["data"], list):
            ticker = data["data"][0]
            if "lastPrice" in ticker:
                price = float(ticker["lastPrice"])
                process_price(price)

    except Exception as e:
        print("Message error:", e)

def on_open(ws):
    print("WebSocket connected")
    sub = {
        "op": "subscribe",
        "args": [f"tickers.{SYMBOL}"]
    }
    ws.send(json.dumps(sub))

def start_ws():
    while True:
        try:
            ws = websocket.WebSocketApp(
                "wss://stream.bybit.com/v5/public/linear",
                on_open=on_open,
                on_message=on_message
            )
            ws.run_forever()
        except Exception as e:
            print("WebSocket restart:", e)
            time.sleep(5)

# ================= FLASK =================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ================= MAIN =================

if __name__ == "__main__":
    print("Bot started")
    send_telegram("🟢 Бот запущен и работает")

    threading.Thread(target=start_ws, daemon=True).start()

    run_flask()

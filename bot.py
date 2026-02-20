import os
import json
import time
import threading
import requests
import websocket
from flask import Flask

# ================= НАСТРОЙКИ =================
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

THRESHOLD_PERCENT = 5  # % изменения для сигнала

# Временные данные
price_history = {}  # {symbol: last_price}
last_alert = {}     # {symbol: last_alert_price}

# ================= TELEGRAM ==================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)

# ================= SYMBOLS ===================
def get_symbols():
    try:
        url = "https://api.bybit.com/v5/market/instruments-info?category=linear"
        resp = requests.get(url).json()
        symbols = [item["symbol"] for item in resp["result"]["list"] if item["status"]=="Trading"]
        print(f"Получено {len(symbols)} торговых пар")
        return symbols
    except Exception as e:
        print("Ошибка получения списка монет:", e)
        return []

SYMBOLS = get_symbols()

# ================= PRICE LOGIC ===============
def process_price(symbol, price):
    price_history.setdefault(symbol, price)
    last = last_alert.get(symbol, price)
    change_percent = ((price - last) / last) * 100

    if abs(change_percent) >= THRESHOLD_PERCENT:
        # Формируем список Pump/Dump для сообщения
        direction = "Pump" if change_percent > 0 else "Dump"
        color = "🟩" if change_percent > 0 else "🟥"
        message = f"{color} {direction} {symbol} — {price:.4f} ({change_percent:.2f}%)"
        send_telegram(message)
        last_alert[symbol] = price

# ================= WEBSOCKET =================
def on_message(ws, message):
    try:
        data = json.loads(message)
        if "data" in data:
            price = float(data["data"]["lastPrice"])
            symbol = data["data"]["symbol"]
            process_price(symbol, price)
    except Exception as e:
        print("Ошибка обработки сообщения:", e)

def on_error(ws, error):
    print("WebSocket ошибка:", error)

def on_close(ws, close_status_code, close_msg):
    print("WebSocket закрыт. Переподключение через 5 сек...")
    time.sleep(5)
    start_websocket()

def on_open(ws):
    print("WebSocket подключен")
    args = [f"tickers.{symbol}" for symbol in SYMBOLS]
    subscribe_message = {"op": "subscribe", "args": args}
    ws.send(json.dumps(subscribe_message))

def start_websocket():
    ws = websocket.WebSocketApp(
        "wss://stream.bybit.com/v5/public/linear",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

# ================= FLASK =====================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running 24/7 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ================= MAIN =====================
if __name__ == "__main__":
    if not TOKEN or not CHAT_ID:
        print("Ошибка: TOKEN или CHAT_ID не заданы")
        exit(1)

    print("Бот запущен")

    # Запускаем Flask в отдельном потоке
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Запускаем WebSocket
    start_websocket()

import json
import time
import threading
import os
import requests
import websocket
from flask import Flask

# ================= НАСТРОЙКИ =================

BOT_TOKEN = os.getenv("TOKEN")       # На Railway установлен TOKEN
CHAT_ID = os.getenv("CHAT_ID")

# Список монет (в примере три, остальные можно добавить вручную)
SYMBOLS = ["BTCUSDT", "ETHUSDT", "RPLUSDT", "SOL", "XRP", "ENSO", "AZTEC", "HYPE", "DOGE", "MYX", "1000PEPE", "XAUT", "RIVER", "OP", "INJ", "AXS", "ORCA", "SUI", "ADA", "PIPPIN", "RAVE", "BIO", "BCH", "BNB", "VVV", "FARTCOIN", "ZEC", "ARB", "TAO", "LINK", "ENA"]

THRESHOLD_PERCENT = 5          # процент изменения для сигнала
WINDOW_SECONDS = 300           # окно анализа (5 минут)
CHECK_INTERVAL = 1             # проверка каждую секунду

# ============================================

price_history = {symbol: [] for symbol in SYMBOLS}
last_alert_time = {symbol: 0 for symbol in SYMBOLS}

# ================= TELEGRAM ==================

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)

# ================= PRICE LOGIC ===============

def process_price(symbol, price):
    global price_history, last_alert_time

    current_time = time.time()
    price_history[symbol].append((current_time, price))

    # Удаляем старые данные
    price_history[symbol] = [
        (t, p) for t, p in price_history[symbol]
        if current_time - t <= WINDOW_SECONDS
    ]

    if len(price_history[symbol]) < 2:
        return

    old_price = price_history[symbol][0][1]
    percent_change = ((price - old_price) / old_price) * 100

    if abs(percent_change) >= THRESHOLD_PERCENT:
        if current_time - last_alert_time[symbol] > WINDOW_SECONDS:
            direction = "📈 Рост" if percent_change > 0 else "📉 Падение"
            message = (
                f"{direction} {symbol}\n"
                f"Изменение: {percent_change:.2f}%\n"
                f"Текущая цена: {price}"
            )
            send_telegram(message)
            last_alert_time[symbol] = current_time

# ================= WEBSOCKET =================

def on_message(ws, message):
    try:
        data = json.loads(message)
        if "data" in data:
            for ticker in data["data"]:
                symbol = ticker["symbol"]
                if symbol in SYMBOLS:
                    price = float(ticker["lastPrice"])
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
    # Подписка на несколько монет
    subscribe_message = {
        "op": "subscribe",
        "args": [f"tickers.{symbol}" for symbol in SYMBOLS]
    }
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

    # ================= BYBIT COINS =================
def get_all_symbols():
    try:
        url = "https://api.bybit.com/v2/public/symbols"
        response = requests.get(url, timeout=10)
        data = response.json()
        if "result" in data:
            symbols = [item["name"] for item in data["result"]]
            print("Все доступные пары на Bybit:")
            print(symbols)
            return symbols
        else:
            print("Ошибка получения списка монет:", data)
            return []
    except Exception as e:
        print("Ошибка получения списка монет:", e)
        return []


# ================= FLASK =====================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ================= MAIN ======================

if __name__ == "__main__":
    print("Бот запущен")

    # Получаем все монеты и выводим в терминал
    all_symbols = get_all_symbols()

    # Flask держит контейнер живым
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Запуск WebSocket (можно пока оставить только на BTCUSDT или других вручную)
    start_websocket()

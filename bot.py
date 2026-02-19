import os
import websocket
import json
import threading
import time
import requests

# ====== Переменные окружения ======
TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# ====== Настройки ======
THRESHOLD = 5           # % изменения для сигнала
CHECK_INTERVAL = 1      # интервал проверки (сек)
PUMP_EMOJI = "🟩"
DUMP_EMOJI = "🟥"

# ====== Хранилище последних цен ======
last_prices = {}

# ====== Отправка сообщений в Telegram ======
def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except requests.exceptions.RequestException as e:
        print("Ошибка отправки сообщения:", e)

# ====== Обработка каждого нового сообщения с WebSocket ======
def on_message(ws, message):
    global last_prices
    try:
        data = json.loads(message)
        if "data" not in data:
            return

        pump_list = []
        dump_list = []

        for coin in data["data"]:
            symbol = coin["symbol"]
            price = float(coin["last_price"])

            if symbol not in last_prices:
                last_prices[symbol] = price
                continue

            base_price = last_prices[symbol]
            change_percent = (price - base_price) / base_price * 100

            if abs(change_percent) >= THRESHOLD:
                if change_percent > 0:
                    pump_list.append(f"{PUMP_EMOJI} {symbol} +{round(change_percent,2)}%")
                else:
                    dump_list.append(f"{DUMP_EMOJI} {symbol} {round(change_percent,2)}%")
                last_prices[symbol] = price

        if pump_list or dump_list:
            message_text = ""
            if pump_list:
                message_text += "\n".join(pump_list) + "\n"
            if dump_list:
                message_text += "\n".join(dump_list)
            send_message(message_text)

    except Exception as e:
        print("Ошибка обработки сообщения:", e)

def on_error(ws, error):
    print("WebSocket ошибка:", error)

def on_close(ws):
    print("WebSocket закрыт")

def on_open(ws):
    print("WebSocket подключен")
    # Подписка на все тикеры линейной категории
    subscribe = {"op": "subscribe", "args": ["tickers.BTCUSDT", "tickers/ETHUSDT", "tickers/ALL"]}  
    ws.send(json.dumps(subscribe))

# ====== Запуск WebSocket в отдельном потоке ======
def start_ws():
    ws = websocket.WebSocketApp(
        "wss://stream.bybit.com/realtime_public",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()

if __name__ == "__main__":
    print("Бот запущен...")
    threading.Thread(target=start_ws).start()
    while True:
        time.sleep(10)  # главный поток спит, WebSocket работает

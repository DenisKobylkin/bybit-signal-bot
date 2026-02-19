import os
import json
import time
import threading
import requests
import websocket

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

THRESHOLD = 5  # процент изменения
PUMP = "🟩"
DUMP = "🟥"

last_prices = {}

# ---------- Telegram ----------
def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": CHAT_ID, "text": text}, timeout=10)
    except Exception as e:
        print("Ошибка Telegram:", e)

# ---------- WebSocket ----------
def on_message(ws, message):
    global last_prices

    try:
        data = json.loads(message)

        if "topic" not in data:
            return

        if "data" not in data:
            return

        symbol = data["data"]["symbol"]
        price = float(data["data"]["lastPrice"])

        if symbol not in last_prices:
            last_prices[symbol] = price
            return

        base = last_prices[symbol]
        change = (price - base) / base * 100

        if abs(change) >= THRESHOLD:
            if change > 0:
                msg = f"{PUMP} {symbol} +{round(change,2)}%"
            else:
                msg = f"{DUMP} {symbol} {round(change,2)}%"

            send_message(msg)
            last_prices[symbol] = price

    except Exception as e:
        print("Ошибка обработки:", e)


def on_error(ws, error):
    print("WebSocket ошибка:", error)


def on_close(ws, close_status_code, close_msg):
    print("WebSocket закрыт. Переподключение через 5 секунд...")
    time.sleep(5)
    start_ws()


def on_open(ws):
    print("WebSocket подключен")

    subscribe_message = {
        "op": "subscribe",
        "args": ["tickers"]
    }

    ws.send(json.dumps(subscribe_message))


def start_ws():
    ws = websocket.WebSocketApp(
        "wss://stream.bybit.com/v5/public/linear",
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    ws.run_forever(ping_interval=20, ping_timeout=10)


# ---------- START ----------
if __name__ == "__main__":
    print("Бот запущен...")
    start_ws()

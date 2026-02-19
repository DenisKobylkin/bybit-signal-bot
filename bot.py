import requests
import time
import json
import os

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

THRESHOLD = 5        # процент движения
CHECK_INTERVAL = 10  # проверка каждые 10 секунд
BASE_FILE = "base_prices.json"

BYBIT_URL = "https://api.bybit.com/v5/market/tickers?category=linear"


# ------------------ Telegram ------------------

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)


# ------------------ Работа с базой ------------------

def load_base_prices():
    if os.path.exists(BASE_FILE):
        with open(BASE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_base_prices(base_prices):
    with open(BASE_FILE, "w") as f:
        json.dump(base_prices, f)


# ------------------ Получение рынка ------------------

def get_market_data():
    try:
        response = requests.get(BYBIT_URL, timeout=10)
        data = response.json()
        return data["result"]["list"]
    except Exception as e:
        print("Ошибка API:", e)
        return []


# ------------------ Основная логика ------------------

def check_market(base_prices):
    market = get_market_data()
    pumps = []
    dumps = []

    for coin in market:
        symbol = coin["symbol"]
        current_price = float(coin["lastPrice"])

        # если монеты нет в базе — фиксируем стартовую цену
        if symbol not in base_prices:
            base_prices[symbol] = current_price
            continue

        base_price = base_prices[symbol]
        change_percent = ((current_price - base_price) / base_price) * 100

        if change_percent >= THRESHOLD:
            pumps.append(f"🟢 <b>{symbol}</b>  +{round(change_percent,2)}%")
            base_prices[symbol] = current_price

        elif change_percent <= -THRESHOLD:
            dumps.append(f"🔴 <b>{symbol}</b>  {round(change_percent,2)}%")
            base_prices[symbol] = current_price

    return pumps, dumps


# ------------------ Запуск ------------------

print("Бот запущен...")
base_prices = load_base_prices()

while True:
    pumps, dumps = check_market(base_prices)

    if pumps or dumps:
        message = "🚨 <b>Market Movement 5%</b>\n\n"

        if pumps:
            message += "<b>📈 PUMP:</b>\n"
            message += "\n".join(pumps)
            message += "\n\n"

        if dumps:
            message += "<b>📉 DUMP:</b>\n"
            message += "\n".join(dumps)

        send_message(message)
        save_base_prices(base_prices)

    time.sleep(CHECK_INTERVAL)

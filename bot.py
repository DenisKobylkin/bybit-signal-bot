import time
import os
import requests
from flask import Flask

# ====== Настройки ======
BOT_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

THRESHOLD_PERCENT = 5   # порог изменения для сигнала
CHECK_INTERVAL = 10     # каждые 10 секунд проверяем

prices = {}             # последний известный ценник

# ====== Telegram ======
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Ошибка Telegram:", e)

# ====== CoinGecko API ======
def get_all_coins():
    url = "https://api.coingecko.com/api/v3/coins/list"
    try:
        r = requests.get(url, timeout=10)
        return r.json()
    except:
        return []

def get_price(ids):
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(ids),
        "vs_currencies": "usd"
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        return r.json()
    except:
        return {}

# ====== Главный цикл ======
def main_loop():
    global prices
    coins = get_all_coins()

    # берем только ограниченное количество (например первые 200)
    ids = [coin["id"] for coin in coins][:200]

    while True:
        current_prices = get_price(ids)

        pump_list = []
        dump_list = []

        for coin_id in ids:
            if coin_id not in current_prices:
                continue

            price_now = current_prices[coin_id]["usd"]
            old = prices.get(coin_id, price_now)
            change = ((price_now - old) / old) * 100

            if abs(change) >= THRESHOLD_PERCENT:
                direction = "📈 Рост" if change > 0 else "📉 Падение"
                if change > 0:
                    pump_list.append(f"🟩 {coin_id} +{change:.2f}%")
                else:
                    dump_list.append(f"🟥 {coin_id} {change:.2f}%")
                prices[coin_id] = price_now

        if pump_list or dump_list:
            message = ""
            if pump_list:
                message += "📊 Pump:\n" + "\n".join(pump_list) + "\n\n"
            if dump_list:
                message += "📉 Dump:\n" + "\n".join(dump_list)
            send_telegram(message)

        time.sleep(CHECK_INTERVAL)

# ====== Flask для Railway ======
app = Flask(__name__)
@app.route("/")
def home():
    return "Bot is running - CoinGecko version"

if __name__ == "__main__":
    print("Запуск бота")
    send_telegram("🟢 Бот запущен (CoinGecko версия)")

    # на Railway просто запускаем цикл
    main_loop()

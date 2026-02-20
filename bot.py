import os
import time
import requests

# ================= НАСТРОЙКИ =================

BOT_TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

THRESHOLD_PERCENT = 5
CHECK_INTERVAL = 60  # проверка каждую минуту

COINS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "solana": "SOL",
    "ripple": "XRP",
    "dogecoin": "DOGE"
}

# =============================================

if not BOT_TOKEN or not CHAT_ID:
    print("TOKEN or CHAT_ID not set")
    exit()

last_prices = {}

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
        print("Ошибка Telegram:", e)

# ================= COINGECKO =================

def get_prices():
    try:
        ids = ",".join(COINS.keys())
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
        response = requests.get(url, timeout=15)

        if response.status_code != 200:
            print("Ошибка API:", response.status_code)
            return None

        return response.json()

    except Exception as e:
        print("Ошибка получения цен:", e)
        return None

# ================= MAIN LOOP =================

def main_loop():
    global last_prices

    send_telegram("Бот запущен (CoinGecko стабильная версия)")

    while True:
        prices = get_prices()

        if prices:
            for coin_id, symbol in COINS.items():

                if coin_id not in prices:
                    continue

                if "usd" not in prices[coin_id]:
                    continue

                price_now = prices[coin_id]["usd"]

                if coin_id in last_prices:
                    old_price = last_prices[coin_id]
                    percent = ((price_now - old_price) / old_price) * 100

                    if abs(percent) >= THRESHOLD_PERCENT:
                        direction = "📈 Рост" if percent > 0 else "📉 Падение"

                        message = (
                            f"{direction} {symbol}\n"
                            f"Изменение: {percent:.2f}%\n"
                            f"Цена: {price_now}$"
                        )

                        send_telegram(message)

                last_prices[coin_id] = price_now

        time.sleep(CHECK_INTERVAL)


# ================= START =====================

if __name__ == "__main__":
    main_loop()

import os
import time
import requests
import threading

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("TOKEN")  # на Railway у тебя TOKEN
CHAT_ID = os.getenv("CHAT_ID")  # shared variable

# Список монет (USDT-пары) — добавь остальные вручную
SYMBOLS = ["BTCUSDT", "ETHUSDT", "RPLUSDT", "SOL", "XRP", "ENSO", "AZTEC", "HYPE", "DOGE", "MYX", "1000PEPE", "XAUT", "RIVER", "OP", "INJ", "AXS", "ORCA", "SUI", "ADA", "PIPPIN", "RAVE", "BIO", "BCH", "BNB", "VVV", "FARTCOIN", "ZEC", "ARB", "TAO", "LINK", "ENA"]

THRESHOLD_PERCENT = 5          # процент изменения для сигнала
CHECK_INTERVAL = 5             # проверка каждые N секунд

# ============================================

last_prices = {}
last_alert_time = {}

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
def check_prices():
    global last_prices, last_alert_time

    try:
        for symbol in SYMBOLS:
            url = f"https://api.bybit.com/v2/public/tickers?symbol={symbol}"
            response = requests.get(url, timeout=10)
            data = response.json()

            if "result" not in data or not data["result"]:
                print(f"Нет данных по {symbol}")
                continue

            current_price = float(data["result"][0]["last_price"])

            # Если раньше не было цены — просто сохраняем
            if symbol not in last_prices:
                last_prices[symbol] = current_price
                last_alert_time[symbol] = 0
                continue

            old_price = last_prices[symbol]
            percent_change = ((current_price - old_price) / old_price) * 100

            if abs(percent_change) >= THRESHOLD_PERCENT:
                now = time.time()
                if now - last_alert_time[symbol] > 300:  # 5 минут между сигналами
                    direction = "📈 Рост" if percent_change > 0 else "📉 Падение"
                    message = (
                        f"{direction} {symbol}\n"
                        f"Изменение: {percent_change:.2f}%\n"
                        f"Текущая цена: {current_price}\n"
                        f"https://www.bybit.com/trade/usdt/{symbol}?ref=NBMDNGN"
                    )
                    send_telegram(message)
                    last_alert_time[symbol] = now

            last_prices[symbol] = current_price

    except Exception as e:
        print("Ошибка при получении цен:", e)

def main_loop():
    print("Бот запущен (REST Bybit)")
    send_telegram("Бот запущен и работает (REST Bybit)")

    while True:
        check_prices()
        time.sleep(CHECK_INTERVAL)

# ================= MAIN ======================
if __name__ == "__main__":
    main_loop()

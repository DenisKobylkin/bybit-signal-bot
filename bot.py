import os
import time
import threading
import requests
import json

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("TOKEN")     # TOKEN из Railway
CHAT_ID = os.getenv("CHAT_ID")     # CHAT_ID из Railway

THRESHOLD_PERCENT = 5              # процент изменения цены для сигнала
CHECK_INTERVAL = 10                # проверка каждые 10 секунд

# ============================================

last_prices = {}    # сохраняем последние цены всех монет

# ================= TELEGRAM ==================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)

# ================= COINGLASS =================
def get_coinglass_prices():
    url = "https://api.coinglass.com/api/pro/v1/futures/tickers"  # примерный endpoint
    headers = {"Accept": "application/json"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        prices = {}
        # Берём символ и цену для каждой монеты
        for item in data.get("data", []):
            symbol = item.get("symbol")
            price = float(item.get("priceUsd", 0))
            if symbol and price > 0:
                prices[symbol] = price
        return prices
    except Exception as e:
        print("Ошибка получения списка монет:", e)
        return {}

# ================= PRICE LOGIC =================
def check_prices():
    global last_prices
    while True:
        current_prices = get_coinglass_prices()
        if not current_prices:
            time.sleep(CHECK_INTERVAL)
            continue

        messages = []

        for symbol, price_now in current_prices.items():
            last_price = last_prices.get(symbol, price_now)
            change_percent = ((price_now - last_price) / last_price) * 100

            if abs(change_percent) >= THRESHOLD_PERCENT:
                direction = "📈 Pump" if change_percent > 0 else "📉 Dump"
                messages.append(f"{direction} {symbol}: {price_now:.4f} USD ({change_percent:.2f}%)")
                # обновляем последнюю цену только при сигнале
                last_prices[symbol] = price_now

        if messages:
            # формируем красивое сообщение
            full_message = "\n".join(messages)
            send_telegram(full_message)
            print("Сигналы отправлены:", full_message)

        time.sleep(CHECK_INTERVAL)

# ================= MAIN ======================
if __name__ == "__main__":
    print("Бот запущен")

    # Отправляем в Telegram, что бот стартовал
    send_telegram("Бот CoinGlass запущен и работает!")

    # Запускаем проверку цен в отдельном потоке
    price_thread = threading.Thread(target=check_prices)
    price_thread.daemon = True
    price_thread.start()

    # Контейнер Railway должен держать процесс живым
    while True:
        time.sleep(60)

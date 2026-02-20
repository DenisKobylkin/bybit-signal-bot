import os
import time
import threading
import requests
from flask import Flask

# ================= НАСТРОЙКИ =================
BOT_TOKEN = os.getenv("TOKEN")   # Ваш TOKEN на Railway
CHAT_ID = os.getenv("CHAT_ID")   # CHAT_ID для Telegram

THRESHOLD_PERCENT = 5          # процент изменения
CHECK_INTERVAL = 60             # проверка каждую минуту
# ============================================

price_history = {}
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

# ================= COINGLASS API =============
COINGLASS_API = "https://api.coinglass.com/api/pro/v1/futures/openInterestAndPrice"

def get_all_symbols():
    """
    Получаем список всех монет и их цены через CoinGlass API.
    """
    try:
        resp = requests.get(COINGLASS_API, timeout=10)
        data = resp.json()
        symbols = {}
        # Пробегаем все монеты и сохраняем их цену
        for coin in data.get("data", []):
            symbol = coin.get("symbol")
            price = coin.get("lastPrice")
            if symbol and price is not None:
                symbols[symbol] = float(price)
        return symbols
    except Exception as e:
        print("Ошибка при получении списка монет:", e)
        return {}

# ================= PRICE LOGIC =================
def check_prices():
    global price_history, last_alert_time
    current_prices = get_all_symbols()
    if not current_prices:
        print("Нет данных по ценам")
        return

    for symbol, price_now in current_prices.items():
        old_price = price_history.get(symbol, price_now)
        percent_change = ((price_now - old_price) / old_price) * 100

        if abs(percent_change) >= THRESHOLD_PERCENT:
            last_time = last_alert_time.get(symbol, 0)
            if time.time() - last_time > 300:  # минимум 5 минут между сигналами
                direction = "📈 Рост" if percent_change > 0 else "📉 Падение"
                message = (
                    f"{direction} {symbol}\n"
                    f"Изменение: {percent_change:.2f}%\n"
                    f"Текущая цена: {price_now}"
                )
                send_telegram(message)
                last_alert_time[symbol] = time.time()

        # обновляем историю
        price_history[symbol] = price_now

# ================= MAIN LOOP =================
def main_loop():
    while True:
        check_prices()
        time.sleep(CHECK_INTERVAL)

# ================= FLASK =====================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ================= START ====================
if __name__ == "__main__":
    print("Бот запущен")

    # Flask поток
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Основной цикл проверки цен
    main_loop()

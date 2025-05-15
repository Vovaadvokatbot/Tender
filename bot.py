import telegram
import requests
import sqlite3
from datetime import datetime
import time
import os

# Настройки
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
PROZORRO_API = "https://public-api.prozorro.gov.ua/tenders"
KEYWORDS = ["обслуживание автопарка", "ремонт автомобилей", "автосервис"]

# Инициализация бота
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Инициализация базы данных
conn = sqlite3.connect("tenders.db")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tenders (
        id TEXT PRIMARY KEY,
        title TEXT,
        url TEXT,
        date_added TEXT
    )
""")
conn.commit()

def fetch_tenders():
    tenders = []
    for keyword in KEYWORDS:
        try:
            params = {"query": keyword}
            response = requests.get(PROZORRO_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            for tender in data.get("data", []):
                tender_id = tender["id"]
                title = tender.get("title", "No title")
                url = f"https://prozorro.gov.ua/tender/{tender_id}"
                
                cursor.execute("SELECT id FROM tenders WHERE id=?", (tender_id,))
                if cursor.fetchone() is None:
                    tenders.append({
                        "id": tender_id,
                        "title": title,
                        "url": url
                    })
        except Exception as e:
            print(f"Ошибка: {e}")
    return tenders

def save_tender(tender):
    cursor.execute("""
        INSERT INTO tenders (id, title, url, date_added)
        VALUES (?, ?, ?, ?)
    """, (tender["id"], tender["title"], tender["url"], datetime.now().isoformat()))
    conn.commit()

def send_notification(tender):
    message = f"Новый тендер на Prozorro:\n{tender['title']}\n{tender['url']}"
    bot.send_message(chat_id=CHAT_ID, text=message)

def main():
    while True:
        print(f"Проверка тендеров: {datetime.now()}")
        tenders = fetch_tenders()
        for tender in tenders:
            save_tender(tender)
            send_notification(tender)
        time.sleep(1800)  # Ждём 30 минут

if __name__ == "__main__":
    main()
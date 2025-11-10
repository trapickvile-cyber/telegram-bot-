import os
import logging
import sqlite3
import requests
import threading
import time
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from flask import Flask
from threading import Thread

# ===== ВЕЧНЫЙ KEEP-ALIVE =====
app = Flask('')

@app.route('/')
def home():
    return f"🤖 Бот работает! {datetime.now().strftime('%H:%M:%S')}"

@app.route('/ping')
def ping():
    return "pong"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Запускаем Flask
flask_thread = Thread(target=run_flask, daemon=True)
flask_thread.start()

# Авто-пинг самого себя
def self_ping():
    while True:
        try:
            # ЗАМЕНИТЕ НА ВАШ URL REPLIT
            your_replit_url = "https://ваш-проект.ваш-юзернейм.repl.co"
            requests.get(f"{your_replit_url}/ping", timeout=10)
            print(f"✅ Self-ping: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"❌ Ping error: {e}")
        time.sleep(60)  # Пинг каждую минуту

ping_thread = Thread(target=self_ping, daemon=True)
ping_thread.start()

# ===== НАСТРОЙКИ БОТА =====
BOT_TOKEN = os.environ['BOT_TOKEN']
ADMIN_ID = int(os.environ.get('ADMIN_ID', '7288020617'))
CHANNEL_ID = os.environ.get('CHANNEL_ID', '@your_channel')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('subscriptions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, subscription_type TEXT, 
                 start_date TEXT, end_date TEXT, status TEXT)''')
    conn.commit()
    conn.close()
    print("✅ База данных готова")

# ===== КЛАВИАТУРЫ =====
def main_keyboard():
    return InlineKeyboardMarkup([[InlineKeyboardButton("Тарифы", callback_data='tariffs')]])

def tariffs_keyboard():
    keyboard = [
        [InlineKeyboardButton("1 месяц - 150 руб", callback_data='month')],
        [InlineKeyboardButton("1 год - 1500 руб", callback_data='year')],
        [InlineKeyboardButton("⏪ Назад", callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===== КОМАНДЫ БОТА =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать, Господин ✨\nвыберите интересующую вас подписку",
        reply_markup=main_keyboard()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'tariffs':
        await query.edit_message_text("Выберите тариф:", reply_markup=tariffs_keyboard())
    elif query.data == 'month':
        await query.edit_message_text(
            "✅ 1 месяц - 150 руб\n\nКарта: **2202 2062 8345 5348**\n\nОтправьте скриншот оплаты."
        )
    elif query.data == 'year':
        await query.edit_message_text(
            "✅ 1 год - 1500 руб\n\nКарта: **2202 2062 8345 5348**\n\nОтправьте скриншот оплаты."
        )
    elif query.data == 'back':
        await query.edit_message_text(
            "Добро пожаловать, Господин ✨\nвыберите интересующую вас подписку",
            reply_markup=main_keyboard()
        )

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    username = update.message.from_user.username or "Нет username"
    
    await update.message.reply_text(
        "✅ Оплата принята! Ссылка на канал:\nhttps://t.me/+NJsfaraaivhh0GEy\n\nДобро пожаловать! 🎉"
    )
    
    await context.bot.send_message(
        ADMIN_ID,
        f"💰 Новая оплата от @{username}"
    )
    
    conn = sqlite3.connect('subscriptions.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?, ?)',
              (user_id, username, "month", datetime.now().isoformat(), 
               (datetime.now() + timedelta(days=30)).isoformat(), 'active'))
    conn.commit()
    conn.close()

# ===== АВТО-ПЕРЕЗАПУСК =====
async def restart_bot():
    """Перезапуск при ошибках"""
    print("🔄 Попытка перезапуска...")
    time.sleep(10)
    main()

# ===== ЗАПУСК =====
def main():
    print("🚀 Запуск бота...")
    
    try:
        init_db()
        
        application = Application.builder().token(BOT_TOKEN).build()
        
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_screenshot))
        
        print("✅ Бот запущен!")
        application.run_polling()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("🔄 Перезапуск через 30 секунд...")
        time.sleep(30)
        main()

if __name__ == '__main__':
    main()

import json
import os
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

TOKEN = "8795611922:AAGcFN_4awe8AHx6xjd-g0Ndbyk2RGjy1Tg"

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running!"

menu_keyboard = [
    ["🛍 Products", "💰 My Balance"],
    ["📦 My Orders"],
    ["💳 Top Up", "🏠 Main Menu"]
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup(
        menu_keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Welcome to Sherry Premium Bot 💖",
        reply_markup=reply_markup
    )

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("BOT STARTING...")
    app.run_polling()

if __name__ == "__main__":
    main()

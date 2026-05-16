import json
import os
import threading
from flask import Flask
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

TOKEN = "8795611922:AAHfMunYyaCdXhYWNGS9wEQ8Z1Jlo7Redrw"
ADMIN_ID = 1695384856
DATA_FILE = "shop_data.json"

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

menu_keyboard = [
    ["🛍 Products", "💰 My Balance"],
    ["💳 Top Up", "📦 My Orders"],
    ["🏠 Main Menu"]
]

default_data = {
    "kpay": "09987654321",
    "wave": "09912345678",
    "users": [],
    "balances": {},
    "orders": {},
    "stock": {},
    "topups": {},
    "categories": {
        "1": "Telegram Premium",
        "2": "CapCut",
        "3": "PicsArt"
    },
    "packages": {
        "1": [["3 Month", 42000], ["6 Month", 61000], ["12 Month", 109000]],
        "2": [["1 Month Share", 4000], ["1 Month Private", 8000]],
        "3": [["1 Month", 8000]]
    }
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            saved = json.load(f)
        for k, v in default_data.items():
            saved.setdefault(k, v)
        return saved
    return default_data.copy()

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()
save_data()

def is_admin(uid):
    return uid == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = str(user.id)

    if uid not in data["users"]:
        data["users"].append(uid)

    data["balances"].setdefault(uid, 0)
    data["orders"].setdefault(uid, [])
    save_data()

    text = f"""
👋 Hello {user.first_name}

👤 User Info
ID: {uid}
Username: @{user.username or "No username"}
Balance: {data["balances"][uid]:,} MMK

👇 Menu ကိုရွေးပါ
"""
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)
    )

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📦 Product Categories\n\n"
    kb = []

    for cid, name in data["categories"].items():
        text += f"{cid}. {name}\n"
        kb.append([InlineKeyboardButton(f"{cid}. {name}", callback_data=f"cat_{cid}")])

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    q = query.data
    uid = str(query.from_user.id)
    data["balances"].setdefault(uid, 0)
    data["orders"].setdefault(uid, [])

    if q.startswith("cat_"):
        cid = q.split("_")[1]
        text = f"📦 {data['categories'][cid]}\n\n"
        kb = []

        for i, item in enumerate(data["packages"].get(cid, [])):
            name, price = item
            key = f"{cid}_{i}"
            stock_count = len(data["stock"].get(key, []))
            text += f"📦 {name} - {price:,} MMK (Stock {stock_count})\n"
            kb.append([InlineKeyboardButton(name, callback_data=f"buy_{cid}_{i}")])

        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

    elif q.startswith("buy_"):
        _, cid, idx = q.split("_")
        idx = int(idx)
        name, price = data["packages"][cid][idx]
        key = f"{cid}_{idx}"

        if len(data["stock"].get(key, [])) <= 0:
            await query.message.reply_text("❌ Out of stock")
            return

        if data["balances"][uid] < price:
            await query.message.reply_text("❌ Balance မလောက်ပါ")
            return

        item = data["stock"][key].pop(0)
        data["balances"][uid] -= price
        data["orders"][uid].append(f"{data['categories'][cid]} - {name}")
        save_data()

        await query.message.reply_text(f"""
✅ Order Success

📦 {data['categories'][cid]}
🛍 {name}
💵 {price:,} MMK

🎁 Product:
{item}
""")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)

    data["balances"].setdefault(uid, 0)
    data["orders"].setdefault(uid, [])

    if text == "🛍 Products":
        await show_categories(update, context)

    elif text == "💰 My Balance":
        await update.message.reply_text(f"💰 Balance = {data['balances'][uid]:,} MMK")

    elif text == "💳 Top Up":
        await update.message.reply_text(f"""
💳 Top Up

KBZPay - {data['kpay']}
WavePay - {data['wave']}

Screenshot ပို့ပါ
""")

    elif text == "📦 My Orders":
        orders = data["orders"].get(uid, [])
        if not orders:
            await update.message.reply_text("No Orders")
        else:
            await update.message.reply_text("\n".join(orders))

    elif text == "🏠 Main Menu":
        await start(update, context)

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    msg = await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"💳 New Top Up\nUser ID: {uid}\n\nReply amount only."
    )
    data["topups"][str(msg.message_id)] = uid
    save_data()
    await update.message.reply_text("✅ Screenshot received")

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("""
🛠 Admin Commands

/products
/stock
/addstock 1_0 account
/clearstock 1_0
/setprice 1_0 50000
/setkpay 099999999
/setwave 099999999
/bc message
""")

async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    msg = "🛠 Products\n\n"
    for cid, cname in data["categories"].items():
        msg += f"{cid}. {cname}\n"
        for i, item in enumerate(data["packages"].get(cid, [])):
            msg += f"{cid}_{i} = {item[0]} | {item[1]:,}\n"
        msg += "\n"

    await update.message.reply_text(msg)

async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    msg = "📦 Stock\n\n"
    for key, items in data["stock"].items():
        msg += f"{key} = {len(items)}\n"

    await update.message.reply_text(msg)

async def addstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    try:
        key = context.args[0]
        item = " ".join(context.args[1:])
        data["stock"].setdefault(key, [])
        data["stock"][key].append(item)
        save_data()
        await update.message.reply_text("✅ Stock Added")
    except:
        await update.message.reply_text("/addstock 1_0 account")

async def clearstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    key = context.args[0]
    data["stock"][key] = []
    save_data()
    await update.message.reply_text("✅ Stock Cleared")

async def setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    key = context.args[0]
    price = int(context.args[1])
    cid, idx = key.split("_")
    data["packages"][cid][int(idx)][1] = price
    save_data()
    await update.message.reply_text("✅ Price Updated")

async def setkpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    data["kpay"] = " ".join(context.args)
    save_data()
    await update.message.reply_text("✅ KBZPay Updated")

async def setwave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    data["wave"] = " ".join(context.args)
    save_data()
    await update.message.reply_text("✅ WavePay Updated")

async def bc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    msg = " ".join(context.args)
    ok = 0
    fail = 0

    for uid in data["users"]:
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg)
            ok += 1
        except:
            fail += 1

    await update.message.reply_text(f"✅ Sent: {ok}\n❌ Failed: {fail}")

def main():
    threading.Thread(target=run_web, daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.PHOTO, receive_photo))

    print("BOT STARTING...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

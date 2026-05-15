import json
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

TOKEN = "8795611922:AAGcFN_4awe8AHx6xjd-g0Ndbyk2RGjy1Tg"
ADMIN_ID = 1695384856
DATA_FILE = "shop_data.json"

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot is running"

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
        "3": "Alight Motion",
        "4": "PicsArt",
        "5": "ChatGPT",
        "6": "Canva",
        "7": "Outline VPN"
    },
    "packages": {
        "1": [["3 Month", 42000], ["6 Month", 61000], ["12 Month", 109000]],
        "2": [["1 Month Share", 4000], ["1 Month Private", 8000]],
        "3": [["1 Month Premium", 5000]],
        "4": [["1 Month", 8000]],
        "5": [["ChatGPT Plus 1 Month", 15000]],
        "6": [["Canva Pro 1 Month", 3000]],
        "7": [["Outline VPN 1 Month", 3000]]
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

def is_admin(user_id):
    return user_id == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "No username"

    if user_id not in data["users"]:
        data["users"].append(user_id)

    data["balances"].setdefault(user_id, 0)
    data["orders"].setdefault(user_id, [])
    save_data()

    text = f"""
👋 Hello {update.effective_user.first_name}

👤 User Info
🆔 ID: {user_id}
👤 Username: @{username}
💰 Balance: {data["balances"][user_id]:,} MMK

👇 Menu ကိုရွေးပါ
"""
    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(menu_keyboard, resize_keyboard=True)
    )

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📦 Product Categories\n\n"
    keyboard = []

    for key, name in data["categories"].items():
        text += f"{key}. {name}\n"
        keyboard.append([InlineKeyboardButton(f"{key}. {name}", callback_data=f"cat_{key}")])

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_packages(message, cat_id):
    if cat_id not in data["categories"]:
        await message.reply_text("❌ Category မရှိပါ။")
        return

    text = f"📦 {data['categories'][cat_id]}\n\n"
    keyboard = []

    for i, item in enumerate(data["packages"].get(cat_id, [])):
        name, price = item
        stock_key = f"{cat_id}_{i}"
        stock_count = len(data["stock"].get(stock_key, []))

        if stock_count <= 0:
            text += f"📦 {name} - {price:,} MMK ❌ Out of stock\n"
        else:
            text += f"📦 {name} - {price:,} MMK (Stock {stock_count})\n"

        keyboard.append([InlineKeyboardButton(name, callback_data=f"buy_{cat_id}_{i}")])

    keyboard.append([InlineKeyboardButton("◀ Back", callback_data="back")])
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    keyboard = [
        [InlineKeyboardButton("📦 Products", callback_data="admin_products")],
        [InlineKeyboardButton("📊 Stock", callback_data="admin_stock")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_bc")],
        [InlineKeyboardButton("💰 Add Balance", callback_data="admin_balance")],
        [InlineKeyboardButton("🧹 Clear Stock", callback_data="admin_clear")],
        [InlineKeyboardButton("⚙ Admin Help", callback_data="admin_help")]
    ]

    await update.message.reply_text("🛠 Admin Panel", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    datax = query.data
    user_id = str(query.from_user.id)

    data["balances"].setdefault(user_id, 0)
    data["orders"].setdefault(user_id, [])

    if datax.startswith("cat_"):
        cat_id = datax.split("_")[1]
        await show_packages(query.message, cat_id)

    elif datax == "back":
        text = "📦 Product Categories\n\n"
        keyboard = []
        for key, name in data["categories"].items():
            text += f"{key}. {name}\n"
            keyboard.append([InlineKeyboardButton(f"{key}. {name}", callback_data=f"cat_{key}")])
        await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif datax.startswith("buy_"):
        _, cat_id, pkg_index = datax.split("_")
        pkg_index = int(pkg_index)

        pkg_name, price = data["packages"][cat_id][pkg_index]
        stock_key = f"{cat_id}_{pkg_index}"

        if len(data["stock"].get(stock_key, [])) <= 0:
            await query.message.reply_text("❌ Out of stock")
            return

        if data["balances"][user_id] < price:
            await query.message.reply_text(
                f"❌ Balance မလောက်ပါ\n\n💰 Balance = {data['balances'][user_id]:,}\n💵 Price = {price:,}"
            )
            return

        delivery = data["stock"][stock_key].pop(0)
        data["balances"][user_id] -= price

        order_text = f"{data['categories'][cat_id]} - {pkg_name} - {price:,} MMK"
        data["orders"][user_id].append(order_text)
        save_data()

        await query.message.reply_text(
            f"""
✅ Order Success

📦 {data['categories'][cat_id]}
🛍 {pkg_name}

💵 Price = {price:,}
💰 Balance = {data['balances'][user_id]:,}

🎁 Product

{delivery}
"""
        )

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🛒 New Order\n\n👤 User = {user_id}\n📦 Product = {pkg_name}\n💵 Price = {price:,}"
        )

    elif datax == "admin_products":
        await query.message.reply_text("/products")

    elif datax == "admin_stock":
        await query.message.reply_text("/stock")

    elif datax == "admin_bc":
        await query.message.reply_text("Usage:\n/bc your message")

    elif datax == "admin_balance":
        await query.message.reply_text("Reply topup screenshot with amount")

    elif datax == "admin_clear":
        await query.message.reply_text("Usage:\n/clearstock 2_0")

    elif datax == "admin_help":
        await query.message.reply_text(admin_help_text())

async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "No username"
    photo_id = update.message.photo[-1].file_id

    sent = await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_id,
        caption=f"""
💳 New Top Up

👤 User = {user_id}
📛 Username = @{username}

ဒီ screenshot ကို Reply လုပ်ပြီး amount ရိုက်ပါ

ဥပမာ:
13000
"""
    )

    data["topups"][str(sent.message_id)] = user_id
    save_data()

    await update.message.reply_text("✅ Screenshot received")

async def addstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    try:
        parts = update.message.text.split(" ", 2)
        stock_key = parts[1]
        item = parts[2]
    except:
        await update.message.reply_text("/addstock 2_0 email@gmail.com:pass")
        return

    data["stock"].setdefault(stock_key, [])
    data["stock"][stock_key].append(item)
    save_data()

    await update.message.reply_text(f"✅ Stock Added\n\nKey = {stock_key}\nTotal = {len(data['stock'][stock_key])}")

async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    msg = "📦 Stock List\n\n"
    for cat_id, pkg_list in data["packages"].items():
        msg += f"{data['categories'].get(cat_id, cat_id)}\n"
        for i, item in enumerate(pkg_list):
            name, price = item
            key = f"{cat_id}_{i}"
            count = len(data["stock"].get(key, []))
            msg += f"{key} = {name} | {count}\n"
        msg += "\n"

    await update.message.reply_text(msg)

async def clearstock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("/clearstock 2_0")
        return

    key = context.args[0]
    data["stock"][key] = []
    save_data()

    await update.message.reply_text(f"✅ Cleared {key}")

async def products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    msg = "🛠 Products\n\n"
    for cat_id, cat_name in data["categories"].items():
        msg += f"{cat_id}. {cat_name}\n"
        for i, item in enumerate(data["packages"].get(cat_id, [])):
            name, price = item
            msg += f"{cat_id}_{i} = {name} | {price:,}\n"
        msg += "\n"

    await update.message.reply_text(msg)

async def setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    try:
        key = context.args[0]
        new_price = int(context.args[1])
        cat_id, pkg_index = key.split("_")
        pkg_index = int(pkg_index)

        data["packages"][cat_id][pkg_index][1] = new_price
        save_data()
        await update.message.reply_text(f"✅ New Price = {new_price:,}")
    except:
        await update.message.reply_text("/setprice 2_0 7000")

async def addpackage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    try:
        cat_id = context.args[0]
        price = int(context.args[-1])
        pkg_name = " ".join(context.args[1:-1])

        data["packages"].setdefault(cat_id, [])
        data["packages"][cat_id].append([pkg_name, price])
        save_data()

        new_index = len(data["packages"][cat_id]) - 1
        await update.message.reply_text(f"✅ Package Added\nKey = {cat_id}_{new_index}")
    except:
        await update.message.reply_text("/addpackage 2 PackageName 6000")

async def bc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    text = update.message.text.replace("/bc ", "")

    if text == "/bc":
        await update.message.reply_text("Usage:\n/bc your message")
        return

    success = 0
    failed = 0

    for user_id in data["users"]:
        try:
            await context.bot.send_message(chat_id=int(user_id), text=text)
            success += 1
        except:
            failed += 1

    await update.message.reply_text(f"✅ Broadcast Finished\n\n✅ Success = {success}\n❌ Failed = {failed}")

async def setkpay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("/setkpay 09987654321")
        return

    data["kpay"] = context.args[0]
    save_data()
    await update.message.reply_text(f"✅ KBZPay Updated\n\n{data['kpay']}")

async def setwave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("/setwave 09912345678")
        return

    data["wave"] = context.args[0]
    save_data()
    await update.message.reply_text(f"✅ WavePay Updated\n\n{data['wave']}")

def admin_help_text():
    return """
🛠 Admin Commands

/products
/stock

/addstock 2_0 account

ဥပမာ:
/addstock 2_0 email@gmail.com:123456

/clearstock 2_0

/setprice 2_0 7000

/addpackage 2 NewPackage 6000

/setkpay 09987654321
/setwave 09912345678

/bc your message

/admin
"""

async def adminhelp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text(admin_help_text())

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_id = str(update.effective_user.id)

    if user_id not in data["users"]:
        data["users"].append(user_id)

    data["balances"].setdefault(user_id, 0)
    data["orders"].setdefault(user_id, [])
    save_data()

    if update.effective_user.id == ADMIN_ID and update.message.reply_to_message:
        replied_id = str(update.message.reply_to_message.message_id)

        if replied_id in data["topups"]:
            try:
                amount = int(text.replace(",", "").strip())
            except:
                await update.message.reply_text("Amount only")
                return

            target = data["topups"][replied_id]
            data["balances"][target] = data["balances"].get(target, 0) + amount
            save_data()

            await update.message.reply_text(f"✅ Approved {amount:,}")
            await context.bot.send_message(
                chat_id=int(target),
                text=f"✅ Top Up Approved\n\n💰 Amount = {amount:,}\n💵 Balance = {data['balances'][target]:,}"
            )
            return

    if text == "🛍 Products":
        await show_categories(update, context)

    elif text == "💰 My Balance":
        await update.message.reply_text(f"💰 Balance = {data['balances'][user_id]:,}")

    elif text == "💳 Top Up":
        await update.message.reply_text(
            f"""
💳 Top Up

KBZPay - {data['kpay']}
WavePay - {data['wave']}

Screenshot ပို့ပါ
"""
        )

    elif text == "📦 My Orders":
        if not data["orders"][user_id]:
            await update.message.reply_text("No Orders")
        else:
            msg = "📦 Orders\n\n"
            for i, order in enumerate(data["orders"][user_id], start=1):
                msg += f"{i}. {order}\n"
            await update.message.reply_text(msg)

    elif text == "🏠 Main Menu":
        await start(update, context)

    else:
        await update.message.reply_text("Menu ကိုရွေးပါ")

def main():
    threading.Thread(target=run_web, daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("adminhelp", adminhelp))
    app.add_handler(CommandHandler("products", products))
    app.add_handler(CommandHandler("stock", stock))
    app.add_handler(CommandHandler("addstock", addstock))
    app.add_handler(CommandHandler("clearstock", clearstock))
    app.add_handler(CommandHandler("setprice", setprice))
    app.add_handler(CommandHandler("addpackage", addpackage))
    app.add_handler(CommandHandler("setkpay", setkpay))
    app.add_handler(CommandHandler("setwave", setwave))
    app.add_handler(CommandHandler("bc", bc))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, receive_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("BOT STARTING...")
    app.run_polling()

if __name__ == "__main__":
    main()

import os
import json
from flask import Flask, request
import telebot
from telebot import types

TOKEN = "8795611922:AAHfMunYyaCdXhYWNGS9wEQ8Z1Jlo7Redrw"
ADMIN_ID = 1695384856
RENDER_URL = "https://sherryprebot.onrender.com"
DATA_FILE = "shop_data.json"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

default_data = {
    "kpay": "09987654321",
    "wave": "09912345678",
    "users": [],
    "balances": {},
    "orders": {},
    "stock": {},
    "topups": {},
    "categories": {"1": "Telegram Premium", "2": "CapCut", "3": "PicsArt"},
    "packages": {
        "1": [["3 Month", 42000], ["6 Month", 61000], ["12 Month", 109000]],
        "2": [["1 Month Share", 4000], ["1 Month Private", 8000]],
        "3": [["1 Month", 8000]]
    }
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            d = json.load(f)
        for k, v in default_data.items():
            d.setdefault(k, v)
        return d
    return default_data.copy()

data = load_data()

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def is_admin(uid):
    return uid == ADMIN_ID

def menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🛍 Products", "💰 My Balance")
    kb.row("💳 Top Up", "📦 My Orders")
    kb.row("🏠 Main Menu")
    return kb

@bot.message_handler(commands=["start"])
def start(msg):
    uid = str(msg.from_user.id)
    if uid not in data["users"]:
        data["users"].append(uid)
    data["balances"].setdefault(uid, 0)
    data["orders"].setdefault(uid, [])
    save_data()

    username = msg.from_user.username or "No username"
    bot.send_message(
        msg.chat.id,
        f"""👋 Hello {msg.from_user.first_name}

👤 User Info
ID: {uid}
Username: @{username}
Balance: {data["balances"][uid]:,} MMK

👇 Menu ကိုရွေးပါ""",
        reply_markup=menu()
    )

@bot.message_handler(commands=["admin"])
def admin(msg):
    if not is_admin(msg.from_user.id):
        return
    bot.send_message(msg.chat.id, """🛠 Admin Commands

/products
/stock
/addstock 1_0 account
/clearstock 1_0
/setprice 1_0 50000
/setkpay 099999999
/setwave 099999999
/bc message
""")

@bot.message_handler(commands=["products"])
def products(msg):
    if not is_admin(msg.from_user.id):
        return
    text = "🛠 Products\n\n"
    for cid, cname in data["categories"].items():
        text += f"{cid}. {cname}\n"
        for i, p in enumerate(data["packages"].get(cid, [])):
            text += f"{cid}_{i} = {p[0]} | {p[1]:,}\n"
        text += "\n"
    bot.send_message(msg.chat.id, text)

@bot.message_handler(commands=["stock"])
def stock(msg):
    if not is_admin(msg.from_user.id):
        return
    text = "📦 Stock\n\n"
    for cid, packs in data["packages"].items():
        text += f"{data['categories'].get(cid, cid)}\n"
        for i, p in enumerate(packs):
            key = f"{cid}_{i}"
            stock = len(data['stock'].get(key, []))
            stock_text = f"✅ Stock {stock}" if stock > 0 else "❌ Stock Out"
            text += f"{key} = {p[0]} | {stock_text}\n"
        text += "\n"
    bot.send_message(msg.chat.id, text)

@bot.message_handler(commands=["addstock"])
def addstock(msg):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.split(" ", 2)
    if len(parts) < 3:
        bot.reply_to(msg, "/addstock 1_0 account")
        return
    key, item = parts[1], parts[2]
    data["stock"].setdefault(key, []).append(item)
    save_data()
    bot.reply_to(msg, f"✅ Stock Added\n{key} = {len(data['stock'][key])}")

@bot.message_handler(commands=["clearstock"])
def clearstock(msg):
    if not is_admin(msg.from_user.id):
        return
    parts = msg.text.split()
    if len(parts) < 2:
        bot.reply_to(msg, "/clearstock 1_0")
        return
    data["stock"][parts[1]] = []
    save_data()
    bot.reply_to(msg, "✅ Stock Cleared")

@bot.message_handler(commands=["setprice"])
def setprice(msg):
    if not is_admin(msg.from_user.id):
        return
    try:
        _, key, price = msg.text.split()
        cid, idx = key.split("_")
        data["packages"][cid][int(idx)][1] = int(price)
        save_data()
        bot.reply_to(msg, "✅ Price Updated")
    except:
        bot.reply_to(msg, "/setprice 1_0 50000")

@bot.message_handler(commands=["setkpay"])
def setkpay(msg):
    if not is_admin(msg.from_user.id):
        return
    data["kpay"] = msg.text.replace("/setkpay", "").strip()
    save_data()
    bot.reply_to(msg, f"✅ KBZPay Updated\n\n{data['kpay']}")

@bot.message_handler(commands=["setwave"])
def setwave(msg):
    if not is_admin(msg.from_user.id):
        return
    data["wave"] = msg.text.replace("/setwave", "").strip()
    save_data()
    bot.reply_to(msg, f"✅ WavePay Updated\n\n{data['wave']}")

@bot.message_handler(commands=["bc"])
def bc(msg):
    if not is_admin(msg.from_user.id):
        return
    text = msg.text.replace("/bc", "").strip()
    ok = 0
    fail = 0
    for uid in data["users"]:
        try:
            bot.send_message(int(uid), text)
            ok += 1
        except:
            fail += 1
    bot.reply_to(msg, f"✅ Sent: {ok}\n❌ Failed: {fail}")

def show_products(chat_id):
    kb = types.InlineKeyboardMarkup()
    text = "📦 Product Categories\n\n"
    for cid, name in data["categories"].items():
        text += f"{cid}. {name}\n"
        kb.add(types.InlineKeyboardButton(f"{cid}. {name}", callback_data=f"cat_{cid}"))
    bot.send_message(chat_id, text, reply_markup=kb)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    uid = str(call.from_user.id)
    data["balances"].setdefault(uid, 0)
    data["orders"].setdefault(uid, [])

    if call.data.startswith("cat_"):
        cid = call.data.split("_")[1]
        kb = types.InlineKeyboardMarkup()
        text = f"📦 {data['categories'][cid]}\n\n"
        for i, p in enumerate(data["packages"].get(cid, [])):
            key = f"{cid}_{i}"
            stock_count = len(data["stock"].get(key, []))
            stock_text = f"✅ Stock {stock_count}" if stock_count > 0 else "❌ Stock Out"
            text += f"{p[0]} - {p[1]:,} MMK | {stock_text}\n"
            kb.add(types.InlineKeyboardButton(p[0], callback_data=f"buy_{cid}_{i}"))
        bot.send_message(call.message.chat.id, text, reply_markup=kb)

    elif call.data.startswith("buy_"):
        _, cid, idx = call.data.split("_")
        idx = int(idx)

        name, price = data["packages"][cid][idx]

        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("✅ Confirm", callback_data=f"confirm_{cid}_{idx}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data="cancel_buy")
        )

        bot.send_message(
    call.message.chat.id,
    f"""🛒 Buy Confirmation

🎁 Product: {name}
💵 Price: {price:,} MMK

ဝယ်မှာသေချာပြီလား?""",
    reply_markup=kb
)
if call.data.startswith("confirm_"):
        _, cid, idx = call.data.split("_")
        idx = int(idx)
        uid = str(call.from_user.id)

        name, price = data["packages"][cid][idx]
        key = f"{cid}_{idx}"

        if len(data["stock"].get(key, [])) <= 0:
            bot.send_message(call.message.chat.id, "❌ Stock Out")
            return

        if data["balances"][uid] < price:
            bot.send_message(call.message.chat.id, "❌ Balance မလောက်ပါ")
            return

        item = data["stock"][key].pop(0)
        data["balances"][uid] -= price
        data["orders"][uid].append(f"{data['categories'][cid]} - {name}")
        save_data()

        bot.send_message(call.message.chat.id, f"""✅ Order Success

📦 {data['categories'][cid]}
🛍 {name}
💵 {price:,} MMK

🎁 Product:
{item}""")
elif call.data == "cancel_buy":
    bot.send_message(call.message.chat.id, "❌ Order Cancelled")
@bot.message_handler(content_types=["photo"])
def photo(msg):
    uid = str(msg.from_user.id)
    sent = bot.send_photo(
        ADMIN_ID,
        msg.photo[-1].file_id,
        caption=f"💳 New Top Up\nUser ID: {uid}\n\nReply amount only."
    )
    data["topups"][str(sent.message_id)] = uid
    save_data()
    bot.reply_to(msg, "✅ Screenshot received")

@bot.message_handler(func=lambda m: True)
def text(msg):
    uid = str(msg.from_user.id)
    data["balances"].setdefault(uid, 0)
    data["orders"].setdefault(uid, [])

    if msg.reply_to_message and is_admin(msg.from_user.id):
        rid = str(msg.reply_to_message.message_id)
        if rid in data["topups"]:
            try:
                amount = int(msg.text.replace(",", "").strip())
                target = data["topups"][rid]
                data["balances"][target] = data["balances"].get(target, 0) + amount
                save_data()
                bot.reply_to(msg, f"✅ Approved {amount:,}")
                bot.send_message(int(target), f"✅ Top Up Approved\nAmount: {amount:,}\nBalance: {data['balances'][target]:,}")
                return
            except:
                bot.reply_to(msg, "Amount only")
                return

    if msg.text == "🛍 Products":
        show_products(msg.chat.id)
    elif msg.text == "💰 My Balance":
        bot.send_message(msg.chat.id, f"💰 Balance = {data['balances'][uid]:,} MMK")
    elif msg.text == "💳 Top Up":
        bot.send_message(msg.chat.id, f"""💳 Top Up

KBZPay - {data['kpay']}
WavePay - {data['wave']}

Screenshot ပို့ပါ""")
    elif msg.text == "📦 My Orders":
        orders = data["orders"].get(uid, [])
        bot.send_message(msg.chat.id, "\n".join(orders) if orders else "No Orders")
    elif msg.text == "🏠 Main Menu":
        start(msg)

@app.route("/")
def home():
    return "Bot is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://sherryprebot.onrender.com/webhook")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

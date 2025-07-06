import os
import random
import time
import csv
import threading
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatAction
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

BOT_TOKEN = "8094196948:AAHsnG2Z3EmDHpKDlR7sENtRm9xdHddLpgc"
AFFILIATE_LINK = "https://broker-qx.pro/sign-up/?lid=1427258"
ADMIN_ID = 5978928248

PNL_PROFIT_BANNER = "pnl_profit.jpg"
PNL_LOSS_BANNER = "pnl_loss.jpg"

bot = Bot(BOT_TOKEN)

try:
    with open("approved_users.txt", "r") as f:
        approved_users = set(f.read().splitlines())
except FileNotFoundError:
    approved_users = set()

STATS_FILE = "signals.csv"
if not os.path.exists(STATS_FILE):
    with open(STATS_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "signal_id", "result"])

APPROVED_OTC_PAIRS = [
    "AUD/USD (OTC)", "NZD/CAD (OTC)", "USD/ARS (OTC)", "USD/INR (OTC)", "USD/MXN (OTC)", "USD/EQP (OTC)",
    "EUR/GBP (OTC)", "USD/DZD (OTC)", "USD/PHP (OTC)", "AUD/CAD (OTC)", "CAD/CHF (OTC)", "GBP/JPY (OTC)",
    "USD/IDR (OTC)", "USD/BRL (OTC)", "NZD/JPY (OTC)", "AUD/JPY (OTC)", "EUR/SGD (OTC)", "GBP/NZD (OTC)",
    "USD/BDT (OTC)", "USD/JPY (OTC)", "NZD/USD (OTC)", "EUR/JPY (OTC)", "USD/PKR (OTC)", "EUR/NZD (OTC)",
    "USD/NGN (OTC)", "USD/TRY (OTC)", "GBP/CAD (OTC)", "USD/COP (OTC)", "USD/ZAR (OTC)", "GBP/CHF (OTC)",
    "AUD/CHF (OTC)", "EUR/CHF (OTC)", "EUR/USD (OTC)", "AUD/NZD (OTC)", "CHF/JPY (OTC)", "EUR/AUD (OTC)",
    "NZD/CHF (OTC)", "USD/CAD (OTC)", "USD/CHF (OTC)", "GBP/USD (OTC)", "EUR/CAD (OTC)", "GBP/AUD (OTC)"
]

def start(update: Update, context: CallbackContext):
    user_id = str(update.effective_user.id)
    banner_path = "banner.jpg"
    welcome_caption = (
        "🚀 *Welcome, Trader!*\n\n"
        "You’re inside the *Frontmantradez OTC Vault* — the chamber for unstoppable binary trades.\n\n"
        "🔒 Unlock your premium signals and master the art of profit."
    )
    if os.path.exists(banner_path):
        bot.send_photo(chat_id=update.effective_chat.id, photo=open(banner_path, "rb"), caption=welcome_caption, parse_mode="Markdown")
    else:
        update.message.reply_text(welcome_caption, parse_mode="Markdown")
    if user_id not in approved_users:
        keyboard = [
            [InlineKeyboardButton("🔗 Unlock Access", url=AFFILIATE_LINK)],
            [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/owner_master76")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(
            "🚫 *Access Locked*\n\nJoin the inner circle — sign up & contact admin to unlock your vault key.",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return
    keyboard = [
        [InlineKeyboardButton("💹 Get OTC Signal", callback_data="getsignal")],
        [InlineKeyboardButton("📊 My Stats", callback_data="mystats")],
        [InlineKeyboardButton("💎 Broker Link", url=AFFILIATE_LINK)],
        [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/owner_master76")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(
        chat_id=update.effective_chat.id,
        text="✅ *Access Granted!*\n\n🔑 *Vault open.* Tap below to summon your next winning OTC signal.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

def approve(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        update.message.reply_text("❌ Not authorized.")
        return
    if len(context.args) != 1:
        update.message.reply_text("Usage: /approve <user_id>")
        return
    user_id = context.args[0]
    approved_users.add(user_id)
    with open("approved_users.txt", "a") as f:
        f.write(f"{user_id}\n")
    update.message.reply_text(f"✅ User {user_id} approved!")

def expiry_selection(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = str(query.from_user.id)
    if query.data == "mystats":
        show_stats(query, context)
        return
    if user_id not in approved_users:
        bot.send_message(chat_id=query.from_user.id, text="🚫 *Access Locked.*", parse_mode="Markdown")
        return
    keyboard = [
        [InlineKeyboardButton("🕒 1 Min", callback_data="expiry_1"), InlineKeyboardButton("🕔 5 Min", callback_data="expiry_5")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=query.from_user.id, text="⏳ *Choose your preferred expiry time:*", parse_mode="Markdown", reply_markup=reply_markup)

def select_expiry(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    expiry = query.data.replace("expiry_", "")
    context.user_data["expiry"] = expiry
    bot.send_message(chat_id=query.from_user.id, text="📌 *Great! Now, type the OTC pair name you want a signal for:*", parse_mode="Markdown")

def custom_pair_text(update: Update, context: CallbackContext):
    pair = update.message.text.strip()
    if pair not in APPROVED_OTC_PAIRS:
        update.message.reply_text(
            "❌ *Invalid pair name.*\n\nPlease choose a valid OTC pair from the list below:\n" + "\n".join([f"• {p}" for p in APPROVED_OTC_PAIRS]),
            parse_mode="Markdown"
        )
        return
    context.user_data["pair"] = pair
    bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    suspense_time = random.randint(5, 10)
    time.sleep(suspense_time)
    send_demo_signal(update, context, pair)

def send_demo_signal(entity, context: CallbackContext, pair: str):
    expiry = context.user_data.get("expiry", "1")
    direction = random.choice(["CALL", "PUT"])
    signal_id = f"VLT-{random.randint(1000, 9999)}"
    context.user_data["signal_id"] = signal_id
    keyboard = [[InlineKeyboardButton("✅ Profit", callback_data="pnl_profit"), InlineKeyboardButton("❌ Loss", callback_data="pnl_loss")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=entity.effective_chat.id if hasattr(entity, "effective_chat") else entity.from_user.id, text=f"🔮 *Vault Signal Ready!*\n\nPair: `{pair}`\nDirection: *{direction}*\nExpiry: `{expiry} Min`\nSignal ID: `{signal_id}`\n\n🚀 *Execute swiftly — vault advantage engaged!*", parse_mode="Markdown", reply_markup=reply_markup)
    threading.Timer(300, remind_feedback, args=(entity, context)).start()

def remind_feedback(entity, context: CallbackContext):
    if "feedback_given" not in context.user_data:
        bot.send_message(chat_id=entity.effective_chat.id if hasattr(entity, "effective_chat") else entity.from_user.id, text="⏳ *Still waiting for your result — did you book profit or loss?*", parse_mode="Markdown")

def handle_pnl(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    result = "Profit" if query.data == "pnl_profit" else "Loss"
    context.user_data["feedback_given"] = True
    signal_id = context.user_data.get("signal_id", "UNKNOWN")
    user_id = str(query.from_user.id)
    with open(STATS_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([user_id, signal_id, result])
    if result == "Profit":
        banner = PNL_PROFIT_BANNER
        caption = "🔥 *Profit locked in! Vault secured.*"
    else:
        banner = PNL_LOSS_BANNER
        caption = "📉 *Loss noted — vault remains ready.*"
    if os.path.exists(banner):
        bot.send_photo(chat_id=query.from_user.id, photo=open(banner, "rb"), caption=caption, parse_mode="Markdown")
    else:
        bot.send_message(chat_id=query.from_user.id, text=caption, parse_mode="Markdown")

def show_stats(query, context: CallbackContext):
    user_id = str(query.from_user.id)
    wins, losses = 0, 0
    with open(STATS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["user_id"] == user_id:
                if row["result"] == "Profit":
                    wins += 1
                elif row["result"] == "Loss":
                    losses += 1
    total = wins + losses
    win_rate = f"{(wins / total) * 100:.1f}%" if total > 0 else "N/A"
    bot.send_message(chat_id=query.from_user.id, text=f"📊 *Your Vault Stats:*\nWins: {wins}\nLosses: {losses}\nWin Rate: {win_rate}", parse_mode="Markdown")

updater = Updater(BOT_TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("approve", approve))
dp.add_handler(CallbackQueryHandler(expiry_selection, pattern="^(getsignal|mystats)$"))
dp.add_handler(CallbackQueryHandler(select_expiry, pattern="^expiry_"))
dp.add_handler(CallbackQueryHandler(handle_pnl, pattern="^pnl_"))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, custom_pair_text))
print("✅ Frontmantradez OTC Vault Bot is LIVE with aura + pair filter.")
updater.start_polling()
updater.idle()

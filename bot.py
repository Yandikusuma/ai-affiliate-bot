# bot.py
import os
import logging
import time
import threading
import requests
from flask import Flask, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

# ===== CONFIG =====
TOKEN = os.environ.get("TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # contoh: "123456789"
RESTART_DELAY = int(os.environ.get("RESTART_DELAY", "8"))  # detik tunggu sebelum restart

# ====== WELCOME & RULES ======
WELCOME_MESSAGE = (
    "👋 Selamat datang di *AI Affiliate Academy - SirYanz*!\\n\\n"
    "✨ Di sini kita belajar bikin konten affiliate pakai AI: gambar, video, prompt, dan strategi.\\n\\n"
    "📌 Sebelum mulai, baca rules dengan ketik /rules\\n"
    "🎯 Tulis intro singkat (nama + mau belajar apa) biar kita kenal ya.\\n\\n"
    "Semoga betah dan bermanfaat — Team SirYanz 🤖🌿"
)

RULES_TEXT = (
    "*📌 RULES GRUP — AI Affiliate Academy (SirYanz)*\\n\\n"
    "1. Hormati sesama member.\\n"
    "2. No spam & promosi liar.\\n"
    "3. Dilarang jual tools ilegal.\\n"
    "4. Gunakan bahasa sopan.\\n"
    "5. Share insight, bukan hanya minta.\\n"
    "6. Pertanyaan teknis? Sertakan contoh/screenshot.\\n"
    "7. Tidak membahas politik/SARA.\\n"
    "8. Fokus: AI, Affiliate, Prompt, Tools, Konten, Tech.\\n\\n"
    "_Semua keputusan admin bersifat final._"
)

# ===== LOGGING =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== Simple admin notifier =====
def notify_admin(text: str):
    """
    Kirim pesan ke admin via Telegram Bot API (requests).
    Tidak menggunakan Application/Dispatcher agar tetap bisa dipakai saat bot crash.
    """
    if not TOKEN or not ADMIN_CHAT_ID:
        logger.warning("TOKEN atau ADMIN_CHAT_ID belum diset. Notifikasi admin dilewatkan.")
        return
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {"chat_id": ADMIN_CHAT_ID, "text": text}
        resp = requests.post(url, data=payload, timeout=10)
        if resp.status_code != 200:
            logger.warning("Gagal kirim notifikasi admin: %s %s", resp.status_code, resp.text)
    except Exception as e:
        logger.exception("Exception saat kirim notifikasi admin: %s", e)

# ===== Flask health server (dipakai UptimeRobot) =====
app = Flask("health_server")

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

def run_health_server():
    # Railway biasanya jalankan web server di port yang disediakan oleh env PORT
    port = int(os.environ.get("PORT", "5000"))
    # jalankan flask di thread terpisah (debug False)
    app.run(host="0.0.0.0", port=port, debug=False)

# ====== BOT HANDLERS ======
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hai! Aku bot AI Affiliate Academy. Ketik /rules untuk lihat tata tertib.")

async def rules_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_markdown(RULES_TEXT)

async def new_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_members = update.message.new_chat_members
    for member in new_members:
        if member.is_bot:
            continue
        name = member.full_name or member.username or "Teman baru"
        text = f"👋 Hai *{name}*!\n\n{WELCOME_MESSAGE}"
        keyboard = InlineKeyboardMarkup.from_row([
            InlineKeyboardButton("Baca Rules", callback_data="show_rules"),
            InlineKeyboardButton("Intro Template", callback_data="intro_template")
        ])
        await update.effective_chat.send_message(text, reply_markup=keyboard, parse_mode="Markdown")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "show_rules":
        await query.message.reply_markdown(RULES_TEXT)
    elif query.data == "intro_template":
        await query.message.reply_text("Contoh intro: `Nama | Mau belajar: Bikin video AI untuk affiliate`")

# ====== Function to build and run the bot once ======
def run_bot_once():
    if not TOKEN:
        logger.error("TOKEN tidak ditemukan. Set environment variable TOKEN dulu.")
        raise RuntimeError("TOKEN missing")
    app_builder = ApplicationBuilder().token(TOKEN).build()

    app_builder.add_handler(CommandHandler("start", start_command))
    app_builder.add_handler(CommandHandler("rules", rules_command))
    app_builder.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_handler))
    app_builder.add_handler(CallbackQueryHandler(callback_handler))

    logger.info("Application built. Running polling...")
    # Run polling (blocking call)
    app_builder.run_polling()

# ====== Supervisor loop: restart on crash & notify admin ======
def main_supervisor():
    # Start health server thread
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    notify_admin("🔁 Bot deploy started (supervisor up).")
    while True:
        try:
            notify_admin("✅ Bot starting (polling)...")
            run_bot_once()
        except Exception as e:
            # Kirim notif error & stacktrace ringkas
            logger.exception("Bot crashed with exception: %s", e)
            short = f"❗ Bot crashed: {e}"
            notify_admin(short)
            # delay sebelum restart agar tidak tight-loop
            time.sleep(RESTART_DELAY)
            notify_admin("♻️ Restarting bot now...")
            continue
        else:
            # jika run_bot_once berakhir tanpa exception (tidak umum), keluar loop
            logger.info("run_bot_once finished gracefully.")
            notify_admin("ℹ️ Bot process finished gracefully.")
            break

if __name__ == "__main__":
    main_supervisor()

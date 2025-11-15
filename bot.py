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



# -----------------------
# /tools - tampil produk & link Lynk.id
# -----------------------
LYNK_URL = "https://lynk.id/siryanz/1mzez3ze9wlj"



# ====== WELCOME & RULES ======
WELCOME_MESSAGE = (
    "👋 Selamat datang di *AI Affiliate Academy - SirYanz*!\n\n"
    "✨ Di sini kita belajar bikin konten affiliate pakai AI: gambar, video, prompt, dan strategi.\n\n"
    "📌 Sebelum mulai, baca rules dengan ketik /rules\n"
    "🎯 Tulis intro singkat (nama + mau belajar apa) biar kita kenal ya.\n\n"
    "Semoga betah dan bermanfaat — Team SirYanz 🤖🌿"
)

RULES_TEXT = (
     "*📌 RULES GRUP — AI Affiliate Academy (SirYanz)*\n\n"
    "1. Hormati sesama member.\n"
    "2. No spam & promosi liar.\n"
    "3. Dilarang jual tools ilegal.\n"
    "4. Gunakan bahasa sopan.\n"
    "5. Share insight, bukan hanya minta.\n"
    "6. Pertanyaan teknis? Sertakan contoh/screenshot.\n"
    "7. Tidak membahas politik/SARA.\n"
    "8. Fokus: AI, Affiliate, Prompt, Tools, Konten, Tech.\n\n"
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
        if resp.status_code == 200:
            logger.info("Notifikasi admin terkirim.")
        else:
            logger.warning("Gagal kirim notifikasi admin: %s %s", resp.status_code, resp.text)
            # jika 403, beri info khusus
            if resp.status_code == 403:
                logger.warning("403 Forbidden: Bot tidak bisa memulai percakapan. Minta admin /start bot di chat pribadi.")
    except Exception as e:
        logger.exception("Exception saat kirim notifikasi admin: %s", e)

# ===== Flask health server (dipakai UptimeRobot) =====
health_app = Flask("health_server")

@health_app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

def run_health_server():
    # Railway biasanya jalankan web server di port yang disediakan oleh env PORT
    port = int(os.environ.get("PORT", "5000"))
    # jalankan flask di thread terpisah (debug False)
    health_app.run(host="0.0.0.0", port=port, debug=False)

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
            InlineKeyboardButton("Perkenalkan Diri", callback_data="intro_template")
        ])
        await update.effective_chat.send_message(text, reply_markup=keyboard, parse_mode="Markdown")

async def tools_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Tampilkan product card untuk Affiliate Product Generator (link Lynk.id).
    """
    title = "🧰 Affiliate Product Generator — 5 in 1"
    subtitle = "Bikin gambar & video produk untuk konten affiliate tanpa sample. Cepat, mudah, dan siap jual!"
    bullets = (
        "• Generate foto produk realistis\n"
        "• Template prompt & caption siap pakai\n"
        "• Export HD untuk TikTok/Marketplace\n"
        "• Cocok untuk affiliate tanpa sample"
    )
    price_note = "Harga terjangkau — lihat detail di Lynk.id"

    text = f"*{title}*\n\n{subtitle}\n\n{bullets}\n\n_{price_note}_"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Beli di Lynk.id", url=LYNK_URL)],
        [InlineKeyboardButton("ℹ️ Detail Produk", callback_data="product_details")],
        [InlineKeyboardButton("🔗 Semua Link", callback_data="show_links")]
    ])

    # Kirim sebagai Markdown, tanpa preview link (karena tombol sudah ada)
    await update.message.reply_markdown(text, reply_markup=keyboard, disable_web_page_preview=True)

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "show_rules":
        await query.message.reply_markdown(RULES_TEXT)
    elif query.data == "intro_template":
        await query.message.reply_text(
            "Biar kita kenal, boleh isi perkenalan singkat pakai template ini:\n\n"
            "Nama:\nDomisili:\nMau belajar:\nPengalaman singkat:\n\n"
            "Ketik /intro untuk ambil template lagi."
        )

    # --- product details ---
    if data == "product_details":
        detail_text = (
            "*Affiliate Product Generator — 5 in 1*\n\n"
            "Fitur utama:\n"
            "• Photo studio mockup (flatlay, white background, lifestyle)\n"
            "• Video short creative (loopable, 9:16) untuk TikTok\n"
            "• Prompt pack & caption templates untuk konversi\n"
            "• Export cepat & berbagai aspect ratio\n\n"
            "Cara beli: tekan tombol *Beli di Lynk.id* di pesan sebelumnya.\n"
            "Butuh demo atau contoh hasil? Reply di grup dan tag @SirYanz"
        )
        await query.message.reply_markdown(detail_text, disable_web_page_preview=True)
        return

    # --- show other links (opsional) ---
    if data == "show_links":
        links_text = (
            "🔗 *Link Penting*\n\n"
            f"• Beli produk: {LYNK_URL}\n"
            "• Group: (masukkan link grup kalau mau)\n"
            "• Tutorial: (link/placeholder)\n\n"
            "Klik tombol *Beli di Lynk.id* untuk langsung membeli."
        )
        await query.message.reply_markdown(links_text, disable_web_page_preview=True)
        return

# ====== Function to build and run the bot once ======
def run_bot_once():
    if not TOKEN:
        logger.error("TOKEN tidak ditemukan. Set environment variable TOKEN dulu.")
        raise RuntimeError("TOKEN missing")
    tg_app = ApplicationBuilder().token(TOKEN).build()

    tg_app.add_handler(CommandHandler("start", start_command))
    tg_app.add_handler(CommandHandler("rules", rules_command))
    tg_app.add_handler(CommandHandler("tools", tools_command))
    tg_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_handler))
    tg_app.add_handler(CallbackQueryHandler(callback_handler))

    logger.info("Application built. Running polling...")
    # Run polling (blocking call)
    tg_app.run_polling()

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

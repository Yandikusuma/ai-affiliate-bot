# bot.py
import os
import logging
import time
import openai
import asyncio
import os
import requests
import random
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


# ====== QOUTES LOCAL =====
LOCAL_QUOTES = [
    "🚀 Proses dulu, hasil belakangan.",
    "🔥 Konsisten kecil lebih penting dari pada motivasi besar.",
    "🎯 Kerjakan 1% hari ini, biar kamu unggul 100% besok.",
    "💡 Kreativitas bukan bakat, tapi kebiasaan.",
    "🤖 AI tidak menggantikan manusia — AI menggantikan yang tidak mau belajar.",
    "🌱 Mulai kecil. Lanjut pelan. Menang besar.",
]

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



# daftar model fallback — urut dari yang paling direkomendasikan untuk teks pendek
HF_MODEL_CANDIDATES = [
    "gpt2",                     # very small, super reliable
    "distilgpt2",               # lightweight & reliable
    "facebook/opt-125m",        # small causal model
    "bigscience/bloom-1b1",     # small-ish
    # tambahkan model lain yang kamu temukan di HuggingFace yang mendukung inference
]

def try_inference_model(model, hf_token, prompt, timeout=20):
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 60, "temperature": 0.8}
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    # raise_for_status supaya error HTTP tertangkap di caller
    resp.raise_for_status()
    data = resp.json()
    # beberapa model kembalikan list-of-dicts with generated_text
    if isinstance(data, list):
        # biasanya first item berisi generated_text
        item = data[0]
        if isinstance(item, dict) and "generated_text" in item:
            return item["generated_text"].strip()
        # kadang model mengembalikan plain string or different structure
        return str(item).strip()
    elif isinstance(data, dict):
        if "generated_text" in data:
            return data["generated_text"].strip()
        # jika dict dengan field 'error' -> raise
        if "error" in data:
            raise RuntimeError(f"HF error: {data['error']}")
        return str(data).strip()
    else:
        return str(data).strip()

def generate_quote_hf_resilient():
    hf_token = os.environ.get("HF_TOKEN")
    prompt = (
        "Buat satu quote motivasi singkat (1 kalimat) untuk content creator atau affiliate. "
        "Tulis ringkas, punchy, dan tambahkan 1 emoji di akhir."
    )

    if not hf_token:
        # kalau token belum diset, langsung fallback lokal
        return random.choice(LOCAL_QUOTES) + " _(no HF token)_"

    # coba model prioritas dulu (opsional: kamu bisa tambahkan preferred model di depan)
    candidates = HF_MODEL_CANDIDATES.copy()
    # contoh: kamu bisa menambahkan model yang sempat gagal sebelumnya ke posisi akhir
    # candidates.insert(0, "google/flan-t5-small")  # jangan pakai kalau sudah 410

    last_err = None
    for model in candidates:
        try:
            text = try_inference_model(model, hf_token, prompt)
            # bersihkan & return
            text = text.replace("\n", " ").strip()
            if len(text) < 3:
                # hasil terlalu pendek -> anggap gagal, lanjutkan
                continue
            return text
        except requests.exceptions.HTTPError as he:
            code = he.response.status_code
            # jika 410/404, berarti model gone -> coba model lain
            last_err = f"HTTP {code} on model {model}: {he}"
            print("generate_quote_hf: model", model, "failed:", last_err)
            time.sleep(0.5)
            continue
        except Exception as e:
            last_err = str(e)
            print("generate_quote_hf: model", model, "error:", last_err)
            time.sleep(0.5)
            continue

    # kalau semua gagal -> fallback lokal
    fallback = random.choice(LOCAL_QUOTES)
    note = f" _(fallback: HF failures, last: {last_err})_"
    return fallback + note


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
    subtitle = "Bikin gambar & video produk untuk konten affiliate tanpa sample. Cepat, mudah, dan siap upload!"
    bullets = (
        "• Generate foto produk realistis\n"
        "• Ubah Gaya Pose Model\n"
        "• Export HD untuk TikTok/Marketplace\n"
        "• Cocok untuk affiliate tanpa sample"
    )
    price_note = "Harga terjangkau — lihat detail di Lynk.id"

    text = f"*{title}*\n\n{subtitle}\n\n{bullets}\n\n_{price_note}_"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Beli di Lynk.id", url=LYNK_URL)],
        [InlineKeyboardButton("ℹ️ Detail Produk", callback_data="product_details")],
        # [InlineKeyboardButton("🔗 Semua Link", callback_data="show_links")]
    ])

    # Kirim sebagai Markdown, tanpa preview link (karena tombol sudah ada)
    await update.message.reply_markdown(text, reply_markup=keyboard, disable_web_page_preview=True)

async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    waiting = await update.message.reply_text("🔄 Membuat quote gratis dari Hari Ini...")
    quote = generate_quote_hf_resilient()
    await waiting.edit_text(f"✨ *Quote AI*\n\n_{quote}_", parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *AI Affiliate Academy — Help Menu*\n\n"
        "Berikut daftar perintah yang bisa kamu gunakan:\n\n"
        "• /start – Cek apakah bot aktif\n"
        "• /rules – Lihat aturan grup\n"
        "• /intro – Ambil template perkenalan\n"
        "• /tools – Lihat tools rekomendasi\n"
        "• /quote – Quote motivasi Hari Ini\n\n"
        "Klik tombol di bawah untuk akses cepat."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📜 Rules", callback_data="show_rules")],
        [InlineKeyboardButton("🙋 Intro", callback_data="intro_template")],
        [InlineKeyboardButton("🛠️ Tools", callback_data="menu_tools")],
        [InlineKeyboardButton("💬 Quote AI", callback_data="help_quote")],
    ])

    await update.message.reply_markdown(text, reply_markup=keyboard)

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
    if query.data == "product_details":
        detail_text = (
            "*Affiliate Product Generator — 5 in 1*\n\n"
            "Fitur utama:\n"
            "• AFFILIATE Content Generator (flatlay, white background, lifestyle)\n"
            "• AI Pose & Background Generator - Ubah Gaya Pose\n"
            "• Custome GPT PROMT\n"
            "• Gampang digunakan dan pastinya tanpa sampel\n\n"
            "Cara beli: tekan tombol *Beli di Lynk.id* di pesan sebelumnya.\n"
            "Butuh demo atau contoh hasil? Reply di grup dan tag @SirYanz"
        )
        await query.message.reply_markdown(detail_text, disable_web_page_preview=True)
        return

    # --- show other links (opsional) ---
    # if query.data == "show_links":
    #     links_text = (
    #         "🔗 *Link Penting*\n\n"
    #         f"• Beli produk: {LYNK_URL}\n"
    #         "• Group: (masukkan link grup kalau mau)\n"
    #         "• Tutorial: (link/placeholder)\n\n"
    #         "Klik tombol *Beli di Lynk.id* untuk langsung membeli."
    #     )
    #     await query.message.reply_markdown(links_text, disable_web_page_preview=True)
    #     return

    if query.data == "help_quote":
        await query.message.reply_text("Ketik /quote untuk mendapatkan quote motivasi dari AI ⚡")
        return

    if query.data == "menu_tools":
        await query.message.reply_text("Ketik /tools untuk melihat tools rekomendasi 🔧")
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
    tg_app.add_handler(CommandHandler("quote", quote_command))
    tg_app.add_handler(CommandHandler("help", help_command))
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

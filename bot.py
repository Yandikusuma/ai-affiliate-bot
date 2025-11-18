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
import json
from datetime import datetime

# ===== CONFIG =====
TOKEN = os.environ.get("TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # contoh: "123456789"
RESTART_DELAY = int(os.environ.get("RESTART_DELAY", "8"))  # detik tunggu sebelum restart


# ====== QOUTES LOCAL =====
LOCAL_QUOTES = [
    "🎯 Konsisten upload hari ini, konsisten terima komisi di kemudian hari.",
    "🔥 Jangan malu views kecil, yang penting niatmu besar.",
    "🚀 Satu konten lebih berharga dari seribu wacana yang tidak jadi.",
    "💡 Algoritma bisa berubah, tapi kerja kerasmu selalu relevan.",
    "🌱 Setiap video adalah benih, hasilnya tumbuh di waktu yang tak kamu duga.",
    "⚡ Jangan nunggu percaya diri, bikin konten sampai kepercayaan diri terbentuk sendiri.",
    "📈 Views naik itu bonus, proses belajar itu investasi.",
    "🧠 Gagal hari ini cuma data, besok tinggal kamu optimasi.",
    "💪 Capek boleh, berhenti jangan dulu.",
    "🎬 Kontenmu bisa jadi biasa buatmu, tapi bisa sangat berharga buat orang lain.",
    "🌟 Jangan remehkan satu konten, dia bisa jadi pintu rezeki yang tak kamu sangka.",
    "🧩 Tugasmu cuma satu: kirim karya, bukan mikirin semua kemungkinan buruk.",
    "🔍 Kalau kamu fokus bantu orang, algoritma pelan-pelan akan bantu kamu.",
    "📌 Ingat, setiap expert dulu juga nol viewers.",
    "🎧 Biarkan orang lain meremehkan, yang penting kamu tetap berkarya.",
    "🧱 Hari ini satu konten, besok satu lagi, begitu caramu membangun “imperium” kecilmu.",
    "🌊 Engagement naik itu bukan keajaiban, tapi hasil dari konsistensi diam-diam.",
    "🕒 Lebih baik mulai terlambat daripada cuma jadi penonton selamanya.",
    "🪜 Konten pertama mungkin buruk, tapi tanpa konten pertama tidak akan ada konten terbaikmu.",
    "🧲 Bukan tugasmu menyenangkan semua orang, tugasmu menemukan orang yang cocok dengan kontenmu.",
    "🎯 Jangan fokus siapa yang nggak nonton, fokus siapa yang diam-diam terbantu.",
    "🚪 Satu konten bisa membuka pintu peluang yang tidak pernah kamu bayangkan.",
    "🔗 Affiliate itu tentang hubungan, bukan sekadar link.",
    "💸 Komisi besar dimulai dari keberanian posting yang kelihatan sepele.",
    "🧭 Kalau niatmu bantu orang memilih lebih mudah, uang akan ikut mengejar.",
    "📣 Jangan takut menjual, karena mungkin orang memang sedang menunggu rekomendasimu.",
    "🧱 Setiap komisi kecil hari ini melatih mental kamu untuk komisi besar nanti.",
    "🧨 Kalau kamu tidak promosi, orang lain yang akan ambil kesempatanmu.",
    "🧺 Keranjang kuning mereka butuh keberanianmu untuk bicara.",
    "💬 Satu kalimat jujur dari kontenmu bisa lebih kuat daripada iklan mahal.",
    "🌅 Mulai hari dengan satu niat: “Hari ini minimal satu konten tayang”.",
    "😌 Tidak apa-apa kalau belum sempurna, yang penting tidak berhenti.",
    "📚 Setiap konten adalah eksperimen, bukan ujian terakhir.",
    "🎯 Bukan tentang viral hari ini, tapi tentang bertahan bertahun-tahun.",
    "🪙 Kualitas itu penting, tapi keberanian publish jauh lebih mahal.",
    "🔁 Kalau gagal, revisi; kalau berhasil, ulangi.",
    "🏃‍♂️ Kamu bukan terlambat, kamu hanya baru mulai serius.",
    "🧱 Algoritma bisa berat sebelah, tapi kerja konsistenmu tidak akan sia-sia.",
    "💥 Jangan bunuh idemu dengan overthinking sebelum sempat dicoba.",
    "✈️ Kontenmu bisa terbang jauh ke orang yang bahkan tidak kamu kenal, tapi butuh kamu tekan tombol “post”.",
    "🌟 Brandingmu terbentuk dari hal kecil yang kamu ulang terus.",
    "🧱 Setiap like, share, dan save adalah batu bata untuk masa depanmu.",
    "👀 Orang mungkin tidak melihat prosesmu, tapi hasilnya akan bicara.",
    "🎁 Konten gratis yang kamu bagikan hari ini bisa jadi alasan orang belanja lewatmu besok.",
    "🧠 Semakin sering kamu bikin konten, semakin tajam insting marketingmu.",
    "🚦 Kamu tidak harus jago di awal, kamu hanya perlu berani mulai.",
    "🧯 Kalau takut dinilai orang, ingat: mereka juga sibuk dipusingkan hidupnya sendiri.",
    "🌱 Konten kecil hari ini bisa jadi akar penghasilan pasifmu nanti.",
    "📊 Belajar baca data itu penting, tapi jangan lupa gerak dulu baru dianalisis.",
    "🧗 Setiap penolakan dan skip adalah tangga menuju audiens yang tepat.",
    "💎 Jujur dalam review, maka kepercayaan akan jadi aset terbesarmu.",
    "🧲 Jangan kejar viral, kejarlah relevan.",
    "🎯 Audience kecil tapi loyal jauh lebih berharga daripada angka besar tanpa rasa.",
    "🧱 Kamu tidak perlu alat mahal, kamu hanya perlu niat yang tidak gampang pudar.",
    "🚀 Satu improvement kecil tiap hari lebih kuat daripada satu lompatan yang tidak pernah terjadi.",
    "🧠 Skill editing bisa dipelajari, tapi mental konsisten harus kamu latih.",
    "⏳ Waktu akan lewat juga, lebih baik lewat sambil kamu upload daripada cuma scroll.",
    "🔍 Kalau satu jenis konten tidak jalan, itu bukan kamu gagal, itu sinyal untuk geser strategi.",
    "🧭 Jangan bandingkan episode satu perjalananmu dengan episode seratus orang lain.",
    "🧱 Kamu sedang membangun sesuatu yang belum terlihat, tapi nanti akan kamu syukuri.",
    "🎬 Tugasmu bukan sempurna di kamera, tapi tulus di hadapan kamera.",
    "🧩 Kontenmu tidak harus disukai semua orang, cukup berguna bagi orang yang tepat.",
    "🔗 Affiliate sukses itu kombinasi kepercayaan, konsistensi, dan keberanian menawarkan.",
    "💳 Kamu bukan “maksa jualan”, kamu sedang bantu orang menemukan produk yang mereka butuhkan.",
    "🧱 Bangun dulu kepercayaan, komisi akan ikut mengalir.",
    "💭 Kalau kamu sendiri tidak percaya pada kontenmu, bagaimana orang lain bisa yakin untuk klik link-mu.",
    "🌈 Variasikan ide, tapi jangan lupakan identitasmu.",
    "🧠 Konten sederhana tapi rutin sering menang melawan konten kompleks yang jarang.",
    "🌍 Suara kecilmu di internet tetap bisa mengubah hari seseorang.",
    "🚪 Lifetime value penonton sering dimulai dari satu konten random yang mereka lihat di FYP.",
    "🌟 Mungkin hari ini sepi, tapi bisa jadi besok salah satu videomu “dibangunkan” algoritma.",
    "🕹️ Mainkan game content creator dengan sabar, bukan dengan emosi.",
    "🔁 Ulangi hal yang berhasil, bukan hanya mengeluh pada hal yang gagal.",
    "🧱 Setiap hari kamu menunda, kamu mengulur datangnya peluang.",
    "🧯 Kritik pedas bisa melukai ego, tapi bisa juga mengasah kualitas.",
    "📌 Simpan niatmu: bantu dulu, jual belakangan.",
    "🧗 Naik pelan-pelan tetap lebih baik daripada tidak bergerak sama sekali.",
    "🧲 Kamu tidak perlu jadi paling hebat, cukup jadi paling konsisten di niche-mu.",
    "💬 Satu CTA jelas lebih baik daripada sepuluh konten tanpa ajakan apa-apa.",
    "🧠 Jangan hanya bikin konten yang kamu suka, bikin juga konten yang audience-mu butuh.",
    "🌱 Kamu menanam kepercayaan setiap kali jujur dalam review produk.",
    "🔍 Jika hasil belum sesuai, jangan langsung ganti mimpi, ganti dulu strategi.",
    "🧱 “Tidak ada ide” sering kali hanya berarti kamu terlalu takut mencoba ide yang ada.",
    "💪 Ingat, kamu sudah pernah melewati hari-hari sulit sebelumnya, konten sepi ini bukan apa-apa.",
    "🎯 Satu niche jelas lebih kuat daripada seribu arah yang membingungkan.",
    "🧭 Kalau lelah, boleh pelan, tapi jangan balik arah.",
    "📈 Naik turun itu wajar, yang penting garis besarnya tetap menanjak.",
    "🧠 Belajar dari creator lain, tapi jangan lupa tetap jadi dirimu sendiri.",
    "📣 Suaramu unik, dan di luar sana ada orang yang menunggu gaya bicaramu.",
    "🧺 Jangan malu kasih link, bisa jadi itu solusi dari masalah orang lain.",
    "😎 Kamu bukan hanya “content creator”, kamu adalah “problem solver” dengan gaya yang seru.",
    "🎁 Konten bermanfaat adalah hadiah gratis untuk audience, dan kepercayaan mereka adalah hadiah untukmu.",
    "🧱 Setiap hari kamu belajar sedikit, besok strategi affiliate-mu akan jauh lebih tajam.",
    "✨ Kamu tidak perlu ratusan ribu followers untuk mulai menghasilkan.",
    "🧠 Jangan buru-buru bilang “bukan rezeki”, padahal kamu belum konsisten uji konten.",
    "🔗 Link affiliate-mu hanyalah alat, yang membuat orang klik adalah value kontenmu.",
    "📌 Pegang satu prinsip: upload dulu, belajar setelahnya, upgrade di konten berikutnya.",
    "🚀 Ketika kamu serius menggarap satu konten, kamu sedang mendekat ke satu peluang baru.",
    "🌈 Kontenmu mungkin kecil, tapi bisa jadi pengingat besar untuk orang lain.",
    "🏆 Terus muncul di layar orang, sampai mereka percaya kalau kamu layak dipercaya.",
]

# -----------------------
# /tools - tampil produk & link Lynk.id
# -----------------------
LYNK_URL = "https://lynk.id/siryanz/1mzez3ze9wlj"


# ====== TUTORIAL STORAGE ======
TUTORIAL_FILE = os.path.join(os.getcwd(), "tutorials.json")

def load_tutorials():
    try:
        if not os.path.exists(TUTORIAL_FILE):
            return {}
        with open(TUTORIAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.exception("Gagal load tutorials.json: %s", e)
        return {}

def save_tutorials(data: dict):
    try:
        tmp = TUTORIAL_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, TUTORIAL_FILE)
    except Exception as e:
        logger.exception("Gagal save tutorials.json: %s", e)

def normalize_key(name: str) -> str:
    return name.strip().lower()


# ====== WELCOME & RULES ======
WELCOME_MESSAGE = (
    "👋 Selamat datang di *AI Affiliate Academy - SirYanz*!\n\n"
    "✨ Di sini kita belajar bikin konten affiliate pakai AI: gambar, video, prompt, dan strategi.\n\n"
    "📌 Lihat semua fitur bot dengan ketik /help\n"
    "📜 Sebelum mulai, baca rules dengan ketik /rules\n"
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



# def generate_quote_deepinfra_sync():
#     """
#     Synchronous call ke DeepInfra OpenAI-compatible endpoint.
#     Returns text (string). Raise/return fallback on failure.
#     """
#     key = os.environ.get("DEEPINFRA_KEY")
#     if not key:
#         return random.choice(LOCAL_QUOTES) + " _(no DEEPINFRA_KEY)_"

#     url = "https://api.deepinfra.com/v1/openai/chat/completions"
#     headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
#     data = {
#         "model": "allenai/olmOCR-2-7B-1025",  # model contoh; ganti jika mau model lain yang tersedia
#         "messages": [{"role": "user", "content":
#             "Buat 1 quote motivasi singkat (1 kalimat) untuk content creator/affiliate. Tambah 1 emoji."}],
#         "max_tokens": 60,
#         "temperature": 0.8
#     }
#     try:
#         r = requests.post(url, headers=headers, json=data, timeout=15)
#         r.raise_for_status()
#         j = r.json()
#         # struktur mirip OpenAI: j["choices"][0]["message"]["content"]
#         text = j["choices"][0]["message"]["content"].strip()
#         return text
#     except Exception as e:
#         print("generate_quote_deepinfra error:", e)
#         return random.choice(LOCAL_QUOTES) + " _(fallback)_"



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
            InlineKeyboardButton("ℹ️ Help Menu", callback_data="open_help")
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
    quote = random.choice(LOCAL_QUOTES)
    text = f"✨ *Quote Hari Ini*\n\n_{quote}_"
    await update.message.reply_markdown(text)

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
    if query.data == "open_help":
        await query.message.reply_text("Gunakan /help untuk melihat semua fitur bot.")
        return

    if query.data == "help_quote":
        await query.message.reply_text("Ketik /quote untuk mendapatkan quote motivasi hari ini ⚡")
        return

    if query.data == "menu_tools":
        await query.message.reply_text("Ketik /tools untuk melihat tools rekomendasi 🔧")
        return

# ====== TUTORIAL HANDLERS ======
async def list_tutorials_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_tutorials()
    if not data:
        await update.message.reply_text("📭 Belum ada tutorial tersimpan. Admin bisa menambahkan dengan /addtutorial (reply ke video).")
        return
    lines = ["📚 Daftar tutorial:"]
    for key, item in data.items():
        title = item.get("title", "")
        uploader = item.get("uploader_name", "admin")
        ts = item.get("timestamp", "")
        lines.append(f"- {key}  ({title}) — by {uploader} {ts}")
    await update.message.reply_text("\n".join(lines))

async def tutorial_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        # tampilkan petunjuk singkat
        await update.message.reply_text("Usage:\n/tutorials — list semua tutorial\n/tutorial <nama tutorial> — kirim video\nAdmin: /addtutorial <nama> (reply ke pesan video)")
        return
    name = " ".join(args).strip()
    key = normalize_key(name)
    data = load_tutorials()
    item = data.get(key)
    if not item:
        await update.message.reply_text("❌ Tutorial tidak ditemukan. Cek daftar dengan /tutorials")
        return
    file_id = item.get("file_id")
    caption = item.get("title", f"Tutorial: {name}")
    try:
        await update.effective_chat.send_video(item["file_id"], caption=item.get("title", name))
    except Exception as e:
        logger.exception("Error saat mengirim tutorial %s: %s", key, e)
        await update.message.reply_text(f"Terjadi error saat mengirim video: {e}")

async def add_tutorial_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    # cek admin di grup (boleh juga ditambah OWNER_ID check jika perlu)
    try:
        member = await chat.get_member(user.id)
        if member.status not in ("administrator", "creator"):
            await update.message.reply_text("🚫 Hanya admin yang boleh menambah tutorial.")
            return
    except Exception:
        # jika command di PM, tolak (atau implementasikan owner check)
        await update.message.reply_text("Perintah ini hanya bisa dipakai di grup oleh admin.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /addtutorial <nama> (reply ke pesan video yang ingin disimpan)")
        return

    name = " ".join(context.args).strip()
    key = normalize_key(name)

    msg = update.message
    video = None
    if msg.reply_to_message and msg.reply_to_message.video:
        video = msg.reply_to_message.video
    elif msg.video:
        video = msg.video
    elif msg.reply_to_message and msg.reply_to_message.document and getattr(msg.reply_to_message.document, "mime_type", "").startswith("video"):
        video = msg.reply_to_message.document
    elif msg.document and getattr(msg.document, "mime_type", "").startswith("video"):
        video = msg.document

    if not video:
        await update.message.reply_text("Harap reply ke pesan video atau lampirkan video saat menjalankan perintah /addtutorial.")
        return

    file_id = video.file_id
    title = getattr(video, "file_name", None) or f"Tutorial {name}"
    uploader_name = user.full_name or user.username or str(user.id)
    ts = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    data = load_tutorials()
    data[key] = {
        "file_id": file_id,
        "title": title,
        "uploader_id": user.id,
        "uploader_name": uploader_name,
        "timestamp": ts
    }
    save_tutorials(data)
    await update.message.reply_text(f"✅ Tutorial '{name}' berhasil disimpan. (key: {key})\nGunakan /tutorial {name} untuk memanggilnya.")



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
     # tutorial handlers
    tg_app.add_handler(CommandHandler("tutorials", list_tutorials_command))
    tg_app.add_handler(CommandHandler("tutorial", tutorial_command))
    tg_app.add_handler(CommandHandler("addtutorial", add_tutorial_command))
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

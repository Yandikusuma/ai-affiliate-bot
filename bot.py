# bot.py
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)

TOKEN = os.environ.get("TOKEN")

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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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

def main():
    if not TOKEN:
        logger.error("TOKEN tidak ditemukan. Pastikan environment variable TOKEN sudah diset.")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("rules", rules_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member_handler))
    app.add_handler(CallbackQueryHandler(callback_handler))

    logger.info("Bot starting (polling)...")
    app.run_polling()

if __name__ == "__main__":
    main()

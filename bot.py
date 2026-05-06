import os
import logging
import requests
import base64
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

PROMPT = """Kamu adalah ahli gizi yang menganalisis foto makanan.
Ketika menerima foto makanan, balas HANYA dalam format ini:

🍽️ *[Nama Makanan]*
📏 Estimasi Porsi: [berat/ukuran]

🔥 Kalori: [angka] kcal
💪 Protein: [angka] g
🍚 Karbo: [angka] g
🥑 Lemak: [angka] g

📝 Catatan: [1 kalimat singkat nilai gizi makanan ini]

Jika bukan foto makanan, balas: "Maaf, ini bukan foto makanan. Kirim foto makanan ya! 🙏"
Berikan estimasi terbaik meskipun tidak 100% akurat."""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Halo! Saya *Nutrition Bot*.\n\n"
        "📸 Kirim foto makananmu dan saya akan analisis kandungan gizinya!\n\n"
        "Yang bisa saya berikan:\n"
        "• 🔥 Kalori (kcal)\n"
        "• 💪 Protein (g)\n"
        "• 🍚 Karbohidrat (g)\n"
        "• 🥑 Lemak (g)\n\n"
        "Langsung kirim foto aja ya!",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Cara Pakai:*\n\n"
        "1. Foto makananmu\n"
        "2. Kirim ke sini\n"
        "3. Tunggu analisis ~5 detik\n\n"
        "💡 *Tips akurasi:*\n"
        "• Foto dari atas (top-down) lebih akurat\n"
        "• Pastikan makanan terlihat jelas\n"
        "• Sertakan alat makan/tangan untuk estimasi porsi",
        parse_mode="Markdown"
    )

async def analyze_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Menganalisis foto...")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        response = requests.get(file.file_path)
        image_data = base64.standard_b64encode(response.content).decode("utf-8")

        image_part = {
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": image_data
            }
        }

        result = model.generate_content([PROMPT, image_part])
        await msg.edit_text(result.text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error: {e}")
        await msg.edit_text("❌ Gagal menganalisis foto. Coba lagi ya!")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 Kirim foto makananmu untuk dianalisis ya!\n"
        "Ketik /help untuk panduan."
    )

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.PHOTO, analyze_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()

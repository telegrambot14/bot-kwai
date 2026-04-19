import yt_dlp
import os
import asyncio
from uuid import uuid4
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")

MAX_SIZE = 50 * 1024 * 1024  # 50 MB

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "kwai" not in url.lower():
        await update.message.reply_text("Pásame un link de Kwai")
        return

    await update.message.reply_text("📥 Procesando link...")

    base = f"video_{uuid4().hex}"
    outtmpl = f"{base}.%(ext)s"

    ydl_opts = {
        'outtmpl': outtmpl,

        # 🔥 FORMATO MÁS COMPATIBLE CON KWAI
        'format': 'bv*+ba/b',

        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,

        # 🔥 MÁS TOLERANCIA A ERRORES
        'retries': 5,
        'fragment_retries': 5,
        'socket_timeout': 30,

        # 🔥 EVITA SATURAR RAILWAY
        'concurrent_fragment_downloads': 1,

        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        }
    }

    try:
        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)

        filepath = await asyncio.to_thread(_download)

        # Ajuste para asegurar mp4 final
        if not filepath.endswith(".mp4"):
            mp4_path = os.path.splitext(filepath)[0] + ".mp4"
            if os.path.exists(mp4_path):
                filepath = mp4_path

        size = os.path.getsize(filepath)

        await update.message.reply_text("📤 Enviando video...")

        with open(filepath, "rb") as f:
            if size > MAX_SIZE:
                await update.message.reply_document(document=f)
            else:
                await update.message.reply_video(video=f)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

    finally:
        for ext in [".mp4", ".webm", ".mkv"]:
            path = f"{base}{ext}"
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🤖 Bot corriendo...")
app.run_polling()

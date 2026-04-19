import yt_dlp
import os
import asyncio
from uuid import uuid4
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN") or "8725768395:AAFv03Bd-9P-7fAB3TDFbjtttHlRVePhGpU"

# Límite práctico de envío por bot (ajusta si lo necesitas)
MAX_SIZE = 50 * 1024 * 1024  # 50 MB

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if "kwai" not in url.lower():
        await update.message.reply_text("Pásame un link de Kwai")
        return

    await update.message.reply_text("📥 Descargando en máxima calidad...")

    # nombre único por si llegan varios mensajes
    base = f"video_{uuid4().hex}"
    outtmpl = f"{base}.%(ext)s"

    ydl_opts = {
        'outtmpl': outtmpl,
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'retries': 3,
        'fragment_retries': 3,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        }
    }

    try:
        # yt-dlp es bloqueante → muévelo a un hilo
        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                # obtener nombre final generado
                return ydl.prepare_filename(info)

        filepath = await asyncio.to_thread(_download)

        # Asegura extensión final mp4 si se fusionó
        if not filepath.endswith(".mp4"):
            # yt-dlp a veces devuelve el nombre previo; busca el mp4 real
            mp4_path = os.path.splitext(filepath)[0] + ".mp4"
            if os.path.exists(mp4_path):
                filepath = mp4_path

        size = os.path.getsize(filepath)

        # Si es grande, envía como documento (sin compresión)
        with open(filepath, "rb") as f:
            if size > MAX_SIZE:
                await update.message.reply_document(document=f)
            else:
                await update.message.reply_video(video=f)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

    finally:
        # Limpieza segura
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
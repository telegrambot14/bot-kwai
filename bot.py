import yt_dlp
import os
import asyncio
import re
from uuid import uuid4
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ TOKEN no encontrado en variables de entorno")

MAX_SIZE = 50 * 1024 * 1024  # 50 MB


async def descargar(url, outtmpl, formato):
    ydl_opts = {
        'outtmpl': outtmpl,
        'format': formato,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'quiet': True,
        'retries': 5,
        'fragment_retries': 5,
        'socket_timeout': 60,
        'concurrent_fragment_downloads': 1,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0'
        }
    }

    def _download():
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)

    return await asyncio.to_thread(_download)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()

    # 🔥 EXTRAER LINK DESDE TEXTO (Kwai + texto)
    urls = re.findall(r'https?://\S+', text)

    if not urls:
        await update.message.reply_text("Pásame un link de Kwai")
        return

    url = urls[0]

    if not any(x in url.lower() for x in ["kwai", "k.kwai"]):
        await update.message.reply_text("Pásame un link de Kwai")
        return

    await update.message.reply_text("📥 Procesando link...")

    base = f"video_{uuid4().hex}"
    outtmpl = f"{base}.%(ext)s"

    filepath = None

    try:
        # 🔥 INTENTO 1 (mejor calidad)
        try:
            filepath = await descargar(url, outtmpl, 'bv*+ba/b')
        except:
            await update.message.reply_text("⚠️ Reintentando en calidad estándar...")
            filepath = await descargar(url, outtmpl, 'best')

        # Ajuste a mp4
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
        await update.message.reply_text(f"❌ Error final: {str(e)}")

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

print("🤖 Bot corriendo en Render...")
app.run_polling()

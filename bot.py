import os
import logging
import requests
import glob
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import yt_dlp

BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def search_youtube_video(song_name):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": song_name,
        "type": "video",
        "videoCategoryId": "10",
        "key": YOUTUBE_API_KEY,
        "maxResults": 1
    }

    response = requests.get(url, params=params)
    data = response.json()

    if "items" in data and len(data["items"]) > 0:
        video_id = data["items"][0]["id"]["videoId"]
        title = data["items"][0]["snippet"]["title"]
        return video_id, title
    return None, None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    song_name = update.message.text
    chat_id = update.message.chat.id

    await update.message.reply_text(f"🔍 Searching for '{song_name}'...")

    video_id, title = search_youtube_video(song_name)
    if not video_id:
        await update.message.reply_text("❌ Song not found on YouTube.")
        return

    await update.message.reply_text(f"🎵 Downloading '{title}'...")

    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': 'song.%(ext)s',
        'quiet': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'cookiefile': 'cookies.txt', 
    }

    try:
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
    except Exception as e:
        try:
            video_url = f"https://yewtu.be/watch?v={video_id}"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
        except Exception as e2:
            await update.message.reply_text("❌ Failed to download song from both sources.")
            await update.message.reply_text(str(e2))
            print(f"Fallback Error: {e2}")
            return

    try:
        file_path = glob.glob("song.*")[0]
        await context.bot.send_audio(chat_id=chat_id, audio=open(file_path, "rb"), title=title)
        os.remove(file_path)
    except Exception as final_e:
        await update.message.reply_text("❌ Failed to send downloaded song.")
        await update.message.reply_text(str(final_e))
        print(f"Send Error: {final_e}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("✅ Bot is running...")
app.run_polling()

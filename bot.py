import os
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import yt_dlp

# Load tokens from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Function to search YouTube using YouTube Data API v3
def search_youtube_video(song_name):
    search_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": song_name,
        "type": "video",
        "videoCategoryId": "10",  # Music category
        "key": YOUTUBE_API_KEY,
        "maxResults": 1
    }

    response = requests.get(search_url, params=params)
    results = response.json()

    if "items" in results and len(results["items"]) > 0:
        video_id = results["items"][0]["id"]["videoId"]
        video_title = results["items"][0]["snippet"]["title"]
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        return video_url, video_title
    else:
        return None, None

# Main bot message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    song_name = update.message.text
    chat_id = update.message.chat.id

    await update.message.reply_text(f"Searching for '{song_name}'...")

    video_url, title = search_youtube_video(song_name)
    if not video_url:
        await update.message.reply_text("Sorry, couldn't find the song.")
        return

    await update.message.reply_text(f"Downloading: {title}")

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'song.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        await context.bot.send_audio(chat_id=chat_id, audio=open("song.mp3", "rb"), title=title)
        os.remove("song.mp3")
    except Exception as e:
        await update.message.reply_text("Failed to download song.")
        print(f"Error: {e}")

# Start the bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
print("Bot is running...")
app.run_polling()


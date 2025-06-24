import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from youtubesearchpython import VideosSearch
import yt_dlp

# Replace with your actual tokens
BOT_TOKEN = '7690476451:AAEJy8kvSv1Y4GFBHoNY-vZoAgOA1z9Howw'

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Function to download and send song
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    song_name = update.message.text
    chat_id = update.message.chat.id

    await update.message.reply_text(f"Searching for '{song_name}'...")

    # Search YouTube for the song
    search = VideosSearch(song_name, limit=1)
    result = search.result()["result"][0]
    url = result["link"]
    title = result["title"]

    await update.message.reply_text(f"Downloading '{title}'...")

    # Download audio using yt_dlp
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

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Send the audio file
    await context.bot.send_audio(chat_id=chat_id, audio=open("song.mp3", "rb"), title=title)

    # Clean up
    os.remove("song.mp3")

# Run the bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot is running...")
app.run_polling()

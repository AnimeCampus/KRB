from pyrogram import Client, filters
from pyrogram.types import Message
import json

# Replace 'YOUR_API_ID' and 'YOUR_API_HASH' with your actual API credentials obtained from my.telegram.org
API_ID = '19099900'
API_HASH = '2b445de78e5baf012a0793e60bd4fbf5'
BOT_TOKEN = '6206599982:AAFhXRwC0SnPCBK4WDwzdz7TbTsM2hccgZc'

# Initialize the Pyrogram client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


# Dictionary to store user message counts
user_message_counts = {}


# Handler to track message counts
@app.on_message(filters.group)
def track_message_count(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id not in user_message_counts:
        user_message_counts[user_id] = 1
    else:
        user_message_counts[user_id] += 1


# Command handler for /rankings command
@app.on_message(filters.command("rankings", prefixes="/") & filters.group)
def show_rankings(client: Client, message: Message):
    sorted_users = sorted(user_message_counts.items(), key=lambda x: x[1], reverse=True)

    rankings_text = "🏆 Group Message Rankings 🏆\n\n"
    for idx, (user_id, message_count) in enumerate(sorted_users, start=1):
        user = app.get_users(user_id)
        rankings_text += f"{idx}. {user.first_name}: {message_count} messages\n"

    message.reply_text(rankings_text)


if __name__ == "__main__":
    app.run()

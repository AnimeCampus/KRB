import os
import matplotlib.pyplot as plt
import numpy as np
import asyncio
from datetime import date
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

app = Client(
    "boto",
    api_id="YOUR_API_ID",
    api_hash="YOUR_API_HASH",
    bot_token="YOUR_BOT_TOKEN",
)

# In-memory data storage (replace this with MongoDB database)
chatdb = {}


@app.on_message(
    filters.command("start") & ~filters.bot & ~filters.forwarded & filters.private
)
async def start_command(_, message: Message):
    await message.reply_text("Welcome to the AnimeKrew Ranking Bot!\nType /top to see the top rankings.")


@app.on_message(
    ~filters.bot & ~filters.forwarded & filters.group & ~filters.via_bot & ~filters.service
)
async def inc_user(_, message: Message):
    chat = message.chat.id
    user = message.from_user.id
    increase_count(chat, user)
    print(chat, user, "increased")


def increase_count(chat_id, user_id):
    today = str(date.today())
    chat_data = chatdb.setdefault(chat_id, {today: {}})
    user_data = chat_data[today].setdefault(user_id, 0)
    chat_data[today][user_id] = user_data + 1


@app.on_message(
    filters.command("top") & ~filters.bot & ~filters.forwarded & filters.group
)
async def show_top_today(_, message: Message):
    chat = message.chat.id
    today = str(date.today())

    if not chatdb.get(chat) or not chatdb[chat].get(today):
        return await message.reply_text("No data available for today")

    user_data = sorted(chatdb[chat][today].items(), key=lambda x: x[1], reverse=True)[:10]

    t = "🔰 **Today's Top Users :**\n\n"
    pos = 1

    for user_id, count in user_data:
        i = await get_name(app, user_id)  # Replace this with your method to get user names
        t += f"**{pos}.** {i} - {count}\n"
        pos += 1

    total_users = len(chatdb[chat][today])
    total_groups = len(chatdb) - 1  # Subtract 1 to exclude the metadata document

    t += f"\n📈 **Statistics:**\nTotal Users: {total_users}\nTotal Groups: {total_groups}"

    # Create a bar chart for the top users
    users = [await get_name(app, item[0]) for item in user_data]
    scores = [item[1] for item in user_data]

    plt.barh(np.arange(len(users)), scores, align='center', color='skyblue')
    plt.yticks(np.arange(len(users)), users)
    plt.xlabel('Scores')
    plt.title("Today's Top Users")

    # Save the plot to an image
    plt.tight_layout()
    plt.savefig('top_users_chart.png', dpi=300)
    plt.close()

    # Send the chart along with the text
    await message.reply_photo(
        photo='top_users_chart.png',
        caption=t,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Show Photo", callback_data="show_photo")]]
        ),
    )

    os.remove('top_users_chart.png')


@app.on_callback_query(filters.regex("show_photo"))
async def show_photo_callback(_, query: CallbackQuery):
    # Respond with a photo here
    await query.answer("This is the photo response.")
    await query.message.reply_photo("top_users_chart.png")  # Replace with the actual photo URL


# Helper function to get user names (Replace this with your method to get user names)
async def get_name(client, user_id):
    try:
        user = await client.get_users(user_id)
        return f"{user.first_name} {user.last_name}" if user.last_name else user.first_name
    except Exception:
        return "Unknown User"


async def main():
    print("Started")
    await app.start()
    await asyncio.sleep(1)
    await app.stop()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())

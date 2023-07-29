import matplotlib.pyplot as plt
import numpy as np
from utils.db import get_name, increase_count, chatdb
import uvloop
from pyrogram.client import Client
from pyrogram import filters
from datetime import date
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

uvloop.install()
app = Client(
    "boto",
    api_id="19099900",
    api_hash="2b445de78e5baf012a0793e60bd4fbf5",
    bot_token="6206599982:AAFhXRwC0SnPCBK4WDwzdz7TbTsM2hccgZc",
)


@app.on_message(
    filters.command("start")
    & ~filters.bot
    & ~filters.forwarded
    & filters.private
)
async def start_command(_, message: Message):
    # Your logic for handling the /start command goes here
    await message.reply_text("Welcome to the AnimeKrew Ranking Bot!\nType /top to see the top rankings.")


@app.on_message(
    ~filters.bot
    & ~filters.forwarded
    & filters.group
    & ~filters.via_bot
    & ~filters.service
)
async def inc_user(_, message: Message):
    if message.text:
        if (
            message.text.strip() == "/top@AnimeKrewRankingBot"
            or message.text.strip() == "/top"
        ):
            return await show_top_today(_, message)

    chat = message.chat.id
    user = message.from_user.id
    increase_count(chat, user)
    print(chat, user, "increased")


async def show_top_today(_, message: Message):
    print("today top in", message.chat.id)
    chat = chatdb.find_one({"chat": message.chat.id})
    today = str(date.today())

    if not chat:
        return await message.reply_text("No data available")

    if not chat.get(today):
        return await message.reply_text("No data available for today")

    t = "🔰 **Today's Top Users :**\n\n"

    user_data = sorted(chat[today].items(), key=lambda x: x[1], reverse=True)[:10]

    pos = 1
    for i, k in user_data:
        i = await get_name(app, i)
        t += f"**{pos}.** {i} - {k}\n"
        pos += 1

    total_users = len(chat[today])
    total_groups = chatdb.count_documents({}) - 1  # Subtract 1 to exclude the metadata document

    t += f"\n📈 **Statistics:**\nTotal Users: {total_users}\nTotal Groups: {total_groups}"


    # Create a bar chart for the top users
    users = [item[0] for item in user_data]
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
    await message.reply_photo(photo='top_users_chart.png', caption=t)
    os.remove('top_users_chart.png')



@app.on_callback_query(filters.regex("overall"))
async def show_top_overall_callback(_, query: CallbackQuery):
    print("overall top in", query.message.chat.id)
    chat = chatdb.find_one({"chat": query.message.chat.id})

    if not chat:
        return await query.answer("No data available", show_alert=True)

    await query.answer("Processing... Please wait")

    t = "🔰 **Overall Top Users :**\n\n"

    overall_dict = {}
    for i, k in chat.items():
        if i == "chat" or i == "_id":
            continue

        for j, l in k.items():
            if j not in overall_dict:
                overall_dict[j] = l
            else:
                overall_dict[j] += l

    pos = 1
    for i, k in sorted(overall_dict.items(), key=lambda x: x[1], reverse=True)[:10]:
        i = await get_name(app, i)

        t += f"**{pos}.** {i} - {k}\n"
        pos += 1

    await query.message.edit_text(
        t,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Today's Ranking", callback_data="today")]]
        ),
    )


@app.on_callback_query(filters.regex("today"))
async def show_top_today_callback(_, query: CallbackQuery):
    print("today top in", query.message.chat.id)
    chat = chatdb.find_one({"chat": query.message.chat.id})
    today = str(date.today())

    if not chat:
        return await query.answer("No data available", show_alert=True)

    if not chat.get(today):
        return await query.answer("No data available for today", show_alert=True)

    await query.answer("Processing... Please wait")

    t = "🔰 **Today's Top Users :**\n\n"

    pos = 1
    for i, k in sorted(chat[today].items(), key=lambda x: x[1], reverse=True)[:10]:
        i = await get_name(app, i)

        t += f"**{pos}.** {i} - {k}\n"
        pos += 1

    await query.message.edit_text(
        t,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Overall Ranking", callback_data="overall")]]
        ),
    )


print("started")
app.run()

from utils.db import get_name, increase_count, chatdb  # Define these functions and database
import uvloop
from pyrogram import filters
from pyrogram.client import Client
from datetime import date
from pyrogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
import matplotlib.pyplot as plt
import io

uvloop.install()
app = Client(
    "boto",
    api_id="19099900",
    api_hash="2b445de78e5baf012a0793e60bd4fbf5",
    bot_token="6206599982:AAFhXRwC0SnPCBK4WDwzdz7TbTsM2hccgZc",
)


def generate_user_graph(chat_data, user_id, group_name):
    user_messages = chat_data.get(user_id, {})
    dates = list(user_messages.keys())
    message_counts = list(user_messages.values())

    plt.figure(figsize=(10, 6))
    plt.plot(dates, message_counts, marker='o', linestyle='-', color='red')
    plt.xlabel('Date')
    plt.ylabel('Message Count')
    plt.title(f"{group_name} - User Message Count Over Time")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the plot to a buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    return buffer


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
            message.text.strip() == "/top@RankingssBot"
            or message.text.strip() == "/top"
        ):
            return await show_top_today(_, message)
        elif message.text.startswith("/graph"):
            return await generate_user_graph_cmd(_, message)

    chat = message.chat.id
    user = message.from_user.id
    increase_count(chat, user)
    print(chat, user, "increased")


async def show_top_today(_, message: Message):
    print("today top in", message.chat.id)
    chat = chatdb.find_one({"chat": message.chat.id})
    today = str(date.today())

    if not chat:
        return await message.reply_text("no data available")

    if not chat.get(today):
        return await message.reply_text("no data available for today")

    group_name = message.chat.title  # Get the group name
    t = f"🔰 **Today's Top Users in {group_name}:**\n\n"

    pos = 1
    for i, k in sorted(chat[today].items(), key=lambda x: x[1], reverse=True)[:10]:
        i = await get_name(app, i)
        t += f"**{pos}.** {i} - {k} messages today\n"  # Add the message count here
        pos += 1

    overall_count = sum(chat[today].values())
    t += f"\n📈 **Total Messages Today:** {overall_count}\n"

    await message.reply_text(
        t,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Overall Ranking", callback_data="overall")],              
            ]
        ),
    )


# Update the generate_user_graph_cmd function as follows:
import os

async def generate_user_graph_cmd(_, message: Message):
    user_id = message.from_user.id
    chat = chatdb.find_one({"chat": message.chat.id})
    today = str(date.today())

    if not chat:
        return await message.reply_text("No data available")

    if not chat.get(today):
        return await message.reply_text("No data available for today")

    if user_id not in chat[today]:
        return await message.reply_text("You have not sent any messages today.")

    group_name = message.chat.title  # Get the group name
    buffer = generate_user_graph(chat, user_id, group_name)  # Pass the entire chat data

    # Save the plot to a temporary file
    temp_file_path = ""
    with open(temp_file_path, "wb") as file:
        file.write(buffer.getbuffer())

    # Send the graph as a photo
    await app.send_photo(
        message.chat.id,
        photo=temp_file_path,
        caption=f"Graph showing your message count over time in {group_name}",
    )

    # Remove the temporary file
    os.remove(temp_file_path)



@app.on_callback_query(filters.regex("overall"))
async def show_top_overall_callback(_, query: CallbackQuery):
    print("overall top in", query.message.chat.id)
    chat = chatdb.find_one({"chat": query.message.chat.id})

    if not chat:
        return await query.answer("No data available", show_alert=True)

    await query.answer("Processing... Please wait")

    t = "🔰 **Overall Top Users :**\n\n"

    overall_dict = {}
    overall_count = 0
    for i, k in chat.items():
        if i == "chat" or i == "_id":
            continue

        for j, l in k.items():
            if j not in overall_dict:
                overall_dict[j] = l
            else:
                overall_dict[j] += l

            overall_count += l  # Calculate the overall message count here

    pos = 1
    for i, k in sorted(overall_dict.items(), key=lambda x: x[1], reverse=True)[:10]:
        i = await get_name(app, i)
        t += f"**{pos}.** {i} - {k} \n"  # Add the message count here
        pos += 1

    t += f"\n📈 **Total Messages Overall:** {overall_count}\n"

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
        t += f"**{pos}.** {i} - {k} \n"  # Add the message count here
        pos += 1

    overall_count = sum(chat[today].values())
    t += f"\n📈 **Total Messages Today:** {overall_count}\n"

    await query.message.edit_text(
        t,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Overall Ranking", callback_data="overall")],              
            ]
        ),
    )


print("started")
app.run()

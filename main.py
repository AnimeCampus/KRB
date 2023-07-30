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


def generate_group_graph(chat_data, group_name):
    dates = list(chat_data.keys())
    message_counts = [sum(user_messages.values()) for user_messages in chat_data.values()]

    plt.figure(figsize=(10, 6))
    plt.plot(dates, message_counts, marker='o', linestyle='-', color='blue')
    plt.xlabel('Date')
    plt.ylabel('Group Message Count')
    plt.title(f"{group_name} - Group Message Count Over Time")
    plt.xticks(rotation=45)
    plt.tight_layout()

    # Save the plot to a buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()

    return buffer



# Update the /graph command
@app.on_message(
    ~filters.bot
    & ~filters.forwarded
    & filters.group
    & ~filters.via_bot
    & ~filters.service
)
async def inc_user(_, message: Message):
    if message.text:
        if message.text.strip() == "/top@RankingssBot" or message.text.strip() == "/top":
            return await show_top_today(_, message)
        elif message.text.startswith("/graph"):
            return await generate_group_graph_cmd(_, message)  # Change the function name

    chat = message.chat.id
    user = message.from_user.id
    increase_count(chat, user)
    print(chat, user, "increased")


# Create a new function to generate the group's message count graph
async def generate_group_graph_cmd(_, message: Message):
    chat = chatdb.find_one({"chat": message.chat.id})

    if not chat:
        return await message.reply_text("No data available")

    group_name = message.chat.title  # Get the group name
    buffer = generate_group_graph(chat, group_name)  # Pass the entire chat data

    # Send the graph as a photo using the buffer directly
    buffer.name = "group_graph.png"  # Set a name for the file
    await app.send_photo(
        message.chat.id,
        photo=buffer,
        caption=f"Graph showing the group's message count over time in {group_name}",
        )


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

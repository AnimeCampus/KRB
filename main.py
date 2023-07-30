from utils.db import get_name, increase_count, chatdb
import uvloop
from pyrogram.client import Client
from pyrogram import filters
from datetime import date
import matplotlib.pyplot as plt
import io
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

    t = "🔰 **Today's Top Users :**\n\n"

    pos = 1
    for i, k in sorted(chat[today].items(), key=lambda x: x[1], reverse=True)[:10]:
        i = await get_name(app, i)

        t += f"**{pos}.** {i} - {k}\n"
        pos += 1

    await message.reply_text(
        t,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Overall Ranking", callback_data="overall")]]
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

# New "stats" command
@app.on_message(filters.command("stats") & filters.private)
async def show_stats(_, message: Message):
    user_count = len(chatdb.distinct("user"))
    group_count = chatdb.count_documents({"chat": {"$lt": 0}})
    await message.reply_text(f"📊 Total Users: {user_count}\n👥 Total Groups: {group_count}")


# New "broadcast" command
@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_message(_, message: Message):
    if message.from_user.id != 6198858059:
        return await message.reply_text("You are not authorized to use this command.")

    text = message.text.split(" ", 1)[1]
    all_chats = chatdb.find()
    for chat in all_chats:
        try:
            await app.send_message(chat["chat"], text)
        except Exception as e:
            print(f"Error broadcasting to chat {chat['chat']}: {e}")

    await message.reply_text("Broadcast sent to all chats.")


# New "graph" command
@app.on_message(filters.command("graph") & filters.private)
async def generate_graph(_, message: Message):
    chat = chatdb.find_one({"chat": message.chat.id})
    today = str(date.today())

    if not chat:
        return await message.reply_text("No data available")

    if not chat.get(today):
        return await message.reply_text("No data available for today")

    x_labels = []
    y_values = []
    for i, k in sorted(chat[today].items(), key=lambda x: x[1], reverse=True)[:10]:
        i = await get_name(app, i)
        x_labels.append(i)
        y_values.append(k)

    plt.figure(figsize=(10, 6))
    plt.bar(x_labels, y_values)
    plt.xlabel("Users")
    plt.ylabel("Counts")
    plt.title("Top Users Today")
    plt.xticks(rotation=45, ha="right")

    # Save the plot to a buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)

    caption = "🔰 **Today's Top Users**\nTo see overall top users, use /graph overall"
    await app.send_photo(message.chat.id, buf, caption=caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📊 Overall", switch_inline_query_current_chat="overalll")]]))

    # Clear the plot for the next use
    plt.clf()


# Inline query handling for graphs
@app.on_inline_query()
async def inline_query_graphs(client, query):
    if not query.query:
        return

    results = []
    if query.query == "overalll":
        # Generate overall graph
        chat = chatdb.find_one({"chat": query.from_user.id})

        if not chat:
            return

        overall_dict = {}
        for i, k in chat.items():
            if i == "chat" or i == "_id":
                continue

            for j, l in k.items():
                if j not in overall_dict:
                    overall_dict[j] = l
                else:
                    overall_dict[j] += l

        x_labels = []
        y_values = []
        for i, k in sorted(overall_dict.items(), key=lambda x: x[1], reverse=True)[:10]:
            i = await get_name(app, i)
            x_labels.append(i)
            y_values.append(k)

        plt.figure(figsize=(10, 6))
        plt.bar(x_labels, y_values)
        plt.xlabel("Users")
        plt.ylabel("Counts")
        plt.title("Overall Top Users")
        plt.xticks(rotation=45, ha="right")

        # Save the plot to a buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)

        results.append(
            InlineQueryResultPhoto(
                id="overall_graph",
                photo=InputFile(buf, filename="overall_graph.png"),
                caption="🔰 **Overall Top Users**",
            )
        )

        # Clear the plot for the next use
        plt.clf()

    elif query.query == "today":
        # Generate today's graph (same as the graph command)
        chat = chatdb.find_one({"chat": query.from_user.id})
        today = str(date.today())

        if not chat:
            return

        if not chat.get(today):
            return

        x_labels = []
        y_values = []
        for i, k in sorted(chat[today].items(), key=lambda x: x[1], reverse=True)[:10]:
            i = await get_name(app, i)
            x_labels.append(i)
            y_values.append(k)

        plt.figure(figsize=(10, 6))
        plt.bar(x_labels, y_values)
        plt.xlabel("Users")
        plt.ylabel("Counts")
        plt.title("Top Users Today")
        plt.xticks(rotation=45, ha="right")

        # Save the plot to a buffer
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)

        results.append(
            InlineQueryResultPhoto(
                id="today_graph",
                photo=InputFile(buf, filename="today_graph.png"),
                caption="🔰 **Today's Top Users**",
            )
        )

        # Clear the plot for the next use
        plt.clf()

    await query.answer(results)


print("started")
app.run()

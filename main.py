from pymongo.mongo_client import MongoClient
from datetime import date
import uvloop
import matplotlib.pyplot as plt
import asyncio
from io import BytesIO
from pyrogram.client import Client
from pyrogram import filters
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

uri = "mongodb+srv://jarvis:op@cluster0.7tisvwv.mongodb.net/?retryWrites=true&w=majority"
mongo = MongoClient(uri).Rankings
chatdb = mongo.chat


def increase_count(chat, user):
    user = str(user)
    today = str(date.today())
    user_db = chatdb.find_one({"chat": chat})

    if not user_db:
        user_db = {}
    elif not user_db.get(today):
        user_db = {}
    else:
        user_db = user_db[today]

    if user in user_db:
        user_db[user] += 1
    else:
        user_db[user] = 1

    chatdb.update_one({"chat": chat}, {"$set": {today: user_db}}, upsert=True)


name_cache = {}


async def get_name(app, id):
    global name_cache

    if id in name_cache:
        return name_cache[id]
    else:
        try:
            i = await app.get_users(id)
            i = f'{(i.first_name or "")} {(i.last_name or "")}'
            name_cache[id] = i
            return i
        except:
            return id


async def get_first_name(app, user_id):
    user = await app.get_users(user_id)
    if user is not None:
        return user.first_name
    return "Unknown User"


async def get_names_async(app, user_ids):
    tasks = [get_first_name(app, user_id) for user_id in user_ids]
    return await asyncio.gather(*tasks)


async def generate_graph_and_send(chat_id, top_users, chat_counts, app):
    plt.figure(figsize=(10, 6))
    plt.bar(top_users, chat_counts, color="skyblue")
    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Users")
    plt.ylabel("Chat Count")
    plt.title("Today's Top Users")
    plt.tight_layout()

    # Save the graph to a BytesIO object
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)

    # Fetch user first names asynchronously using asyncio.gather
    top_user_names = await get_names_async(app, top_users)

    # Create the caption with usernames and chat counts
    caption = "🔰 **Today's Top Users :**\n\n"
    for i, (user_name, count) in enumerate(zip(top_user_names, chat_counts)):
        caption += f"**{i + 1}.** {user_name} - {count}\n"

    # Send the graph as a photo with the caption to the chat
    await app.send_photo(
        chat_id=chat_id,
        photo=buffer,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Overall Ranking", callback_data="overall")]]
        ),
    )

    # Close the plot to avoid memory leaks
    plt.close()




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

    top_users_data = sorted(chat[today].items(), key=lambda x: x[1], reverse=True)[:10]
    top_users = [user_id for user_id, _ in top_users_data]
    chat_counts = [count for _, count in top_users_data]

    # Generate and send the graph with the caption
    await generate_graph_and_send(query.message.chat.id, top_users, chat_counts, app)

    # No need to update the caption here


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


@app.on_message(
    filters.command("top", prefixes="/")  # Handle the /top command
    & filters.group
)
async def view_top_rankings(_, message: Message):
    chat = message.chat.id
    user = message.from_user.id

    # Ignore messages sent by the bot itself
    me = await app.get_me()
    if user == me.id:
        return

    # Get the top users and their chat counts
    chat_data = chatdb.find_one({"chat": chat})
    today = str(date.today())
    if not chat_data or not chat_data.get(today):
        return await message.reply_text("No data available for today")

    top_users_data = sorted(chat_data[today].items(), key=lambda x: x[1], reverse=True)[:10]
    top_users = [user_id for user_id, _ in top_users_data]
    chat_counts = [count for _, count in top_users_data]

    # Generate and send the graph with the caption
    await generate_graph_and_send(chat, top_users, chat_counts, app)


print("started")
app.run()

from utils.db import get_name, increase_count, chatdb
import uvloop
from pyrogram.client import Client
from PIL import Image
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



# Custom state dictionary to hold user's profile data during profile setup
user_states = {}


# Existing code for inc_user and show_top_today functions


# New "profile" command
@app.on_message(filters.command("profile") & filters.private)
async def set_profile(_, message: Message):
    user_id = message.from_user.id

    if user_id in user_states:
        # User already started setting the profile
        await message.reply_text("You are already setting up your profile.")
    else:
        user_states[user_id] = {}
        user_states[user_id]["name"] = True
        await message.reply_text("Please provide your name.")


# Message handler for setting profile details step by step
@app.on_message(filters.private & ~filters.command("profile"))
async def handle_profile_setup(_, message: Message):
    user_id = message.from_user.id

    if user_id in user_states:
        if user_states[user_id].get("name"):
            # Collect the user's name
            user_states[user_id]["name"] = message.text.strip()
            await message.reply_text("Please provide an optional profile picture.")
        elif user_states[user_id].get("profile_pic"):
            # If the user sent a photo, save it as a profile picture
            photo = message.photo[-1]
            profile_pic = await photo.download()
            user_states[user_id]["profile_pic"] = profile_pic

            # Save profile data to the database
            user_data = {
                "user_id": user_id,
                "name": user_states[user_id]["name"],
                "profile_pic": user_states[user_id]["profile_pic"],
            }
            user_profiles.replace_one({"user_id": user_id}, user_data, upsert=True)

            del user_states[user_id]  # Remove user from state dictionary
            await message.reply_text("Your profile has been saved successfully!")
        else:
            # Invalid input after name, prompt again
            await message.reply_text("Please provide a valid profile picture.")


# New "viewprofile" command
@app.on_message(filters.command("viewprofile") & filters.private)
async def view_profile(_, message: Message):
    user_id = message.from_user.id
    user_data = user_profiles.find_one({"user_id": user_id})

    if not user_data:
        return await message.reply_text("You have not set a profile yet.")

    profile_pic = user_data.get("profile_pic")
    name = user_data.get("name")

    if profile_pic:
        # If a profile picture exists, send it along with the name
        with open(profile_pic, "rb") as file:
            await app.send_photo(message.chat.id, file, caption=name)
    else:
        await message.reply_text(name)


# Inline query handling for user profiles
@app.on_inline_query()
async def inline_query_profiles(client, query):
    user_id = query.from_user.id
    user_data = user_profiles.find_one({"user_id": user_id})

    if user_data:
        name = user_data.get("name")
        profile_pic = user_data.get("profile_pic")

        if profile_pic:
            # If a profile picture exists, send it along with the name
            with open(profile_pic, "rb") as file:
                await app.send_photo(
                    chat_id=query.chat.id,
                    photo=file,
                    caption=name,
                    reply_to_message_id=query.message.message_id,
                )
        else:
            await query.answer([InlineQueryResultArticle("0", name, None, None)])

    else:
        await query.answer(
            [InlineQueryResultArticle("0", "Profile not set.", None, None)]
        )


# Existing code for other commands and functions




print("started")
app.run()

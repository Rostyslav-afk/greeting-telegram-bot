from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import json

TOKEN = "8603217696:AAH0RUSPelgrrABlXTE-3-VqEQmGE8YZy2c"

data_file = "greeting.json"

def save_photo(file_id):
    with open(data_file, "w") as f:
        json.dump({"photo": file_id}, f)

def load_photo():
    try:
        with open(data_file) as f:
            return json.load(f)["photo"]
    except:
        return None

waiting_photo = False

async def setgreeting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_photo
    waiting_photo = True
    await update.message.reply_text("Відправ фото для привітання.")

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_photo
    if waiting_photo:
        file_id = update.message.photo[-1].file_id
        save_photo(file_id)
        waiting_photo = False
        await update.message.reply_text("Фото збережено!")

async def new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_id = load_photo()

    for member in update.message.new_chat_members:
        name = member.username if member.username else member.first_name
        user_id = member.id

        time = datetime.now().strftime("%d %B %Y")

        text = f"""
Привіт у чаті ЗУНР!

ㅤㅤㅤㅤㅤㅤㅤㅤㅤ{name}
Айді: {user_id}

Час приєднання: {time}
"""

        if photo_id:
            await update.message.reply_photo(photo_id, caption=text)
        else:
            await update.message.reply_text(text)

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("setgreeting", setgreeting))
app.add_handler(MessageHandler(filters.PHOTO, photo))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))

app.run_polling()
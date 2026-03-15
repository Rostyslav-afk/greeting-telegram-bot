from dotenv import load_dotenv
load_dotenv()
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import json
import os
import logging

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)    

TOKEN = os.environ.get("8603217696:AAH0RUSPelgrrABlXTE-3-VqEQmGE8YZy2c", "")

data_file = "greeting.json"

def save_data(photo_id, file_type="photo"):
    with open(data_file, "w") as f:
        json.dump({"photo": photo_id, "file_type": file_type}, f)

def load_data():
    try:
        with open(data_file) as f:
            return json.load(f)
    except:
        return {}

async def is_admin(chat_id, user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception as e:
        logger.error(f"Failed to check admin status: {e}")
        return False

verified_admins = {}
waiting_photo = {}

async def setgreeting(update, context):
    chat_type = update.effective_chat.type
    user_id = update.effective_user.id

    if chat_type != "private":
        group_chat_id = update.effective_chat.id
        if not await is_admin(group_chat_id, user_id, context):
            await update.message.reply_text("Тільки адміністратори можуть змінювати налаштування бота.")
            return
        verified_admins[user_id] = group_chat_id
        bot_info = await context.bot.get_me()
        await update.message.reply_text(
            f"Ти підтверджений як адміністратор.\n"
            f"Тепер напиши боту в приватні повідомлення: @{bot_info.username}\n"
            f"Там відправ /setgreeting з прикріпленим фото."
        )
        return

    if user_id not in verified_admins:
        await update.message.reply_text("Спочатку відправ /setgreeting у групі, щоб підтвердити права адміністратора.")
        return

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        save_data(file_id, file_type="photo")
        waiting_photo.pop(user_id, None)
        verified_admins.pop(user_id, None)
        await update.message.reply_text("Фото збережено! Тепер бот буде надсилати його при вітанні нових учасників.")
    elif update.message.document and update.message.document.mime_type and update.message.document.mime_type.startswith("image/"):
        file_id = update.message.document.file_id
        save_data(file_id, file_type="document")
        waiting_photo.pop(user_id, None)
        verified_admins.pop(user_id, None)
        await update.message.reply_text("Фото збережено! Тепер бот буде надсилати його при вітанні нових учасників.")
    else:
        waiting_photo[user_id] = True
        await update.message.reply_text("Відправ фото для привітання.")

async def photo_in_dm(update, context):
    if update.effective_chat.type != "private":
        return
    user_id = update.effective_user.id
    if not waiting_photo.get(user_id) or user_id not in verified_admins:
        return
    file_id = update.message.photo[-1].file_id
    save_data(file_id, file_type="photo")
    waiting_photo.pop(user_id, None)
    verified_admins.pop(user_id, None)
    await update.message.reply_text("Фото збережено! Тепер бот буде надсилати його при вітанні нових учасників.")

async def document_in_dm(update, context):
    if update.effective_chat.type != "private":
        return
    user_id = update.effective_user.id
    if not waiting_photo.get(user_id) or user_id not in verified_admins:
        return
    doc = update.message.document
    if doc and doc.mime_type and doc.mime_type.startswith("image/"):
        save_data(doc.file_id, file_type="document")
        waiting_photo.pop(user_id, None)
        verified_admins.pop(user_id, None)
        await update.message.reply_text("Фото збережено! Тепер бот буде надсилати його при вітанні нових учасників.")

async def new_member(update, context):
    data = load_data()
    photo_id = data.get("photo")
    file_type = data.get("file_type", "photo")
    chat_id = update.message.chat_id

    for member in update.message.new_chat_members:
        name = member.username if member.username else member.first_name
        user_id = member.id
        time = datetime.now().strftime("%d %B %Y")
        text = f"Привіт у чаті ЗУНР {name}!\nАйді: {user_id}\nЧас приєднання: {time}"

        try:
            if photo_id and file_type == "document":
                await context.bot.send_document(chat_id=chat_id, document=photo_id, caption=text)
            elif photo_id:
                await context.bot.send_photo(chat_id=chat_id, photo=photo_id, caption=text)
            else:
                await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception as e:
            logger.error(f"Failed to send greeting: {e}")
            await context.bot.send_message(chat_id=chat_id, text=text)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("setgreeting", setgreeting))
app.add_handler(MessageHandler(filters.PHOTO, photo_in_dm))
app.add_handler(MessageHandler(filters.Document.IMAGE, document_in_dm))
app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
app.run_polling()
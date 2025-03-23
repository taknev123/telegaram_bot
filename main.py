import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from os import getenv
import dotenv
from db import init_db, save_user, get_user, save_match, get_match, delete_match

# Load environment variables
dotenv.load_dotenv()
init_db()

# Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# States
NAME, GENDER, PREF, DESC = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Welcome 😄 What's your name?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Your gender? (male/female)")
    return GENDER

async def get_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['gender'] = update.message.text.lower()
    await update.message.reply_text("Who do you want to match with? (male/female)")
    return PREF

async def get_pref(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['pref'] = update.message.text.lower()
    await update.message.reply_text("Describe yourself in 3 words ✨")
    return DESC

async def get_desc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    context.user_data['desc'] = update.message.text
    save_user(user_id, context.user_data['name'], context.user_data['gender'], context.user_data['pref'], context.user_data['desc'])
    await update.message.reply_text("All set! Type /match to find someone 💘")
    return ConversationHandler.END

async def match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user = get_user(user_id)
    if not user:
        await update.message.reply_text("Please /start and set your profile first.")
        return

    for other in get_user(None):
        other_id = other[0]
        if other_id == user_id:
            continue
        if other[2] == user[3] and other[3] == user[2] and not get_match(user_id):
            save_match(user_id, other_id)
            save_match(other_id, user_id)
            await update.message.reply_text("You've been matched anonymously! Start chatting 💬")
            await context.bot.send_message(chat_id=other_id, text="You've been matched anonymously! Say hi 💌")
            return
    await update.message.reply_text("No match found right now 😢")

async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    match_id = get_match(user_id)
    if match_id:
        await context.bot.send_message(chat_id=match_id, text=f"💬 Anonymous: {update.message.text}")
    else:
        await update.message.reply_text("You're not in a chat. Use /match first.")

async def next(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    match_id = get_match(user_id)
    if match_id:
        delete_match(user_id)
        delete_match(match_id)
        await context.bot.send_message(chat_id=match_id, text="Match ended. You can /match again.")
    await match(update, context)

def main():
    app = Application.builder().token(getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            PREF: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pref)],
            DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_desc)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("match", match))
    app.add_handler(CommandHandler("next", next))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))

    print("🔥 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
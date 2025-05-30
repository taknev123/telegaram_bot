import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
NAME, GENDER, PREF, DESC, CITY, VIBE, INTENT = range(7)

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
    context.user_data['desc'] = update.message.text
    await update.message.reply_text("Which city are you from? 🏙")
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['city'] = update.message.text.lower()
    await update.message.reply_text("What vibe best describes you? (Chill / Energetic / Funny / Introvert / Flirty) 🌈")
    return VIBE

async def get_vibe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['vibe'] = update.message.text.lower()
    await update.message.reply_text("What are you looking for? (Just Vibing / Dating / Serious) 💞")
    return INTENT

async def get_intent(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    context.user_data['intent'] = update.message.text.lower()
    save_user(
        user_id,
        context.user_data['name'],
        context.user_data['gender'],
        context.user_data['pref'],
        context.user_data['desc'],
        context.user_data['city'],
        context.user_data['vibe'],
        context.user_data['intent']
    )
    await update.message.reply_text("All set! Type /match to find someone 💘")
    return ConversationHandler.END

async def match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    chat_type = update.message.chat.type
    user = get_user(user_id)
    if not user:
        await update.message.reply_text("Please /start and set your profile first.")
        return

    best_score = 0
    best_match = None

    for other in get_user(None):
        other_id = other[0]
        if other_id == user_id or get_match(user_id):
            continue
        if other[2] != user[3] or other[3] != user[2]:
            continue

        score = 0
        user_keywords = set(user[4].lower().split())
        other_keywords = set(other[4].lower().split())
        common_keywords = user_keywords & other_keywords
        score += len(common_keywords)  # 1-3 pts

        if user[5] == other[5]:  # city
            score += 4
        if user[6] == other[6]:  # vibe
            score += 3
        if user[7] == other[7]:  # intent
            score += 3

        if score > best_score:
            best_score = score
            best_match = other

    if best_match and best_score >= 7:
        save_match(user_id, best_match[0])
        save_match(best_match[0], user_id)

        if chat_type == "group" or chat_type == "supergroup":
            username1 = update.message.from_user.username
            username2 = context.bot.get_chat(best_match[0]).username
            display1 = f"@{username1}" if username1 else user[1]
            display2 = f"@{username2}" if username2 else best_match[1]

            text = (
                f"💘 {display1} has been matched with {display2}!\n"
                f"💬 About them: \"{best_match[4]}\"\n"
                f"⭐ Match Score: {best_score}/13"
            )

            if username2:
                keyboard = [[InlineKeyboardButton("💬 DM Now", url=f"https://t.me/{username2}")]]
                await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await update.message.reply_text(text)
        else:
            await update.message.reply_text(
                f"🔥 You've been matched with *{best_match[1]}*\n"
                f"💬 About them: \"{best_match[4]}\"\n"
                f"⭐ Match Score: {best_score}/13\n"
                f"Start chatting! Everything you say now will be forwarded anonymously. 💌",
                parse_mode='Markdown')
            await context.bot.send_message(
                chat_id=best_match[0],
                text=(
                    f"🔥 You've been matched with *{user[1]}*\n"
                    f"💬 About them: \"{user[4]}\"\n"
                    f"⭐ Match Score: {best_score}/13\n"
                    f"Start chatting! Everything you say now will be forwarded anonymously. 💌"
                ),
                parse_mode='Markdown')
    else:
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

async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_user(None)
    if not data:
        await update.message.reply_text("No users found.")
        return
    msg = "👥 *Registered Users:*\n"
    for u in data:
        msg += f"\n👤 {u[1]} | {u[2]} → {u[3]} | \"{u[4]}\" | {u[5]}, {u[6]}, {u[7]}"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def show_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = get_user(None)
    if not data:
        await update.message.reply_text("No users/matches found.")
        return
    msg = "💞 *Current Matches:*\n"
    for u in data:
        match = get_match(u[0])
        if match:
            partner = get_user(match)
            if partner:
                msg += f"\n{u[1]} 💘 {partner[1]}"
    await update.message.reply_text(msg, parse_mode='Markdown')

def main():
    app = Application.builder().token(getenv("BOT_TOKEN")).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_gender)],
            PREF: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_pref)],
            DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_desc)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
            VIBE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_vibe)],
            INTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_intent)],
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("match", match))
    app.add_handler(CommandHandler("next", next))
    app.add_handler(CommandHandler("show_users", show_users))
    app.add_handler(CommandHandler("show_matches", show_matches))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message))

    print("🔥 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()

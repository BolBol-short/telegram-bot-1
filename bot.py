import os
import logging

from dotenv import load_dotenv
from google import genai
from google.genai import types
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)

load_dotenv()

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]

gemini = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = (
    "You are a helpful assistant. Answer clearly and directly, in 2-3 sentences."
)

ABOUT_TEXT = (
    "This is a telegram bot. Currently, it is being test and developed by @BolBol-short on Github."
)

chat_histories = {}
MAX_TURNS = 10

# start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(ABOUT_TEXT)

# help command
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Here are your commands:\n/ask - Ask AI for short answers\n/start - start the bot\n/remind - remind the user after certain minutes")

# reminder helper and command
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    await context.bot.send_message(chat_id=job.chat_id, text=f"Reminder: {job.data}")

async def remind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    args = context.args

    if len(args) < 2:
        await update.message.reply_text("Usage: /remind <minutes> <message>")
        return

    try: 
        minutes = float(args[0])
    except ValueError:
        await update.message.reply_text("Value has to be a number of minutes")
        return

    text = " ".join(args[1:])

    context.job_queue.run_once(
        send_reminder,
        when=minutes * 60,
        chat_id=chat_id,
        data=text,
        name=f"reminder-{chat_id}",
    )
    await update.message.reply_text(f"Got it - Reminding in {minutes:g} min")

# AI asking command
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    args = context.args

    if not args:
        await update.message.reply_text("Usage: /ask <question>")
        return

    question = " ".join(args)

    history = chat_histories.get(chat_id, [])
    logging.info(f"History for {chat_id}: {len(history)} past turns")

    conversation = history + [
        types.Content(role="user", parts=[types.Part(text=question)])
    ]


    try:
        res = await gemini.aio.models.generate_content(
            model="gemini-3.6-flash",
            contents=conversation,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                max_output_tokens=800,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )
        answer = res.text

        conversation.append(
            types.Content(role="model", parts=[types.Part(text=answer)])
        )
        chat_histories[chat_id] = conversation[-MAX_TURNS:]

        await update.message.reply_text(f"AI Answered:\n\t{answer}")
    except Exception:
        logging.exception("AI API call failed.")
        await update.message.reply_text("Sorry, something went wrong. Try again, later!")

async def compass(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            text="Open",
            web_app=WebAppInfo(url="https://"),
        )]
    ])
    await update.message.reply_text("Tap to open: ", reply_markup=keyboard)

def register_handlers(app):
    commands = {
        "start": start,
        "help": help,
        "ask": ask,
        "remind": remind,
        "compass": compass,
    }
    for name, callback in commands.items():
        app.add_handler(CommandHandler(name, callback))
    

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    register_handlers(app)
    logging.info("Bot starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
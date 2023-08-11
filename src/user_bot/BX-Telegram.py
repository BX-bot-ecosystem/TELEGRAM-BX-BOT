import logging
import re
import time
import json
from dotenv import load_dotenv
import os
import math
import Lore
import Committees
from utils import db
import utils
import Committees.intro

load_dotenv()
BOT_TOKEN = os.getenv("SAILORE_BX_BOT")

with open(utils.config.ROOT + '/data/Initial.json', encoding='utf-8') as f:
    texts = json.load(f)

utils.Vcheck.telegram()
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

INITIAL, LORE, CONTINUE, COMMITTEES = range(4)



def message_wait(message):
    return math.log(len(message), 10) - 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    for message in texts["start"]:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(message_wait(message))
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    db.add_to_db(update.effective_user)
    return INITIAL

async def generic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Response depending on the message received"""
    message = update.message.text
    keys = texts.keys()
    for key in keys:
        if re.match(key, message.lower()):
            text = texts[key]
            break
    else:
        text = texts["predetermined"]
    for message in text:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(message_wait(message))
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    return INITIAL



def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).build()
    members = Lore.Members()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), MessageHandler(filters.TEXT, start)],
        states={
            INITIAL: [ 
                #Initial state of the bot in which it can be asked about gems, the lore and committees
                Lore.GemHandler.handler,
                MessageHandler(
                    filters.Regex(re.compile(r"l'?ore", re.IGNORECASE)), members.intro
                ),
                MessageHandler(
                    filters.Regex(re.compile(r"com+it+e+s?", re.IGNORECASE)), Committees.intro #added the question marks cuz people tend to mispell this word
                ),
                MessageHandler(filters.TEXT, generic)
            ],
            LORE: [
                #State of the bot in which it can be asked about the different sailore members
                CallbackQueryHandler(members.member)
            ],
            CONTINUE: [
                #State of the bot in which it is asked if it wants to continue asking about sailore members
                CallbackQueryHandler(members.more)
            ],
            COMMITTEES:  Committees.committees
        },
        fallbacks=[MessageHandler(filters.TEXT, generic)],
        per_chat=False
    )
    
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

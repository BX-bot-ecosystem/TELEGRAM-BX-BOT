import re
import time
import math
import Lore
import Committees
import utils
import bx_utils

from dotenv import load_dotenv
import os
load_dotenv()
BOT_TOKEN = os.getenv("SAILORE_BX_BOT")
gc_id = int(os.getenv("GC_ID"))
import json
with open(utils.config.ROOT + '/data/Initial.json', encoding='utf-8') as f:
    texts = json.load(f)

bx_utils.Vcheck.telegram()
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


logger = bx_utils.logger(__name__)

INITIAL, LORE, CONTINUE, COMMITTEES, REQUEST = range(5)



def message_wait(message):
    return math.log(len(message), 10) - 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    for message in texts["start"]:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(message_wait(message))
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    bx_utils.db.add_to_db(update.effective_user)
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

async def request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow users to input requests"""
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="What do you want to tell the tech support")
    return REQUEST

async def manage_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="The support has been informed and it will be taken into consideration")
    await context.bot.send_message(chat_id=gc_id,
                                   text=f'Request from {update.effective_user.name}: \n{request}')


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
                CommandHandler("request", request),
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
            COMMITTEES:  Committees.committees,
            REQUEST: [
                MessageHandler(filters.TEXT, manage_request)
            ]
        },
        fallbacks=[MessageHandler(filters.TEXT, generic)],
        per_chat=False
    )
    
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

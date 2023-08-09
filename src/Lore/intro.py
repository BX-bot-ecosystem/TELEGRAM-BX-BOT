import json
import utils
import time
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import math
INITIAL, LORE, CONTINUE, COMMITTEES = range(4)

with open(utils.config.ROOT + '/data/Initial.json', encoding='utf-8') as f:
    texts = json.load(f)
    
def message_wait(message):
    return math.log(len(message), 10) - 1

async def intro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Tell them a little bit about Sailore and allows them to learn about each of the members"""
    for message in texts["lore"]:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(message_wait(message))
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    return LORE

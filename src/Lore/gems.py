import re
import time

import bx_utils
import utils

from dotenv import load_dotenv
import os
load_dotenv()
BOT_TOKEN = os.getenv("SAILORE_BX_BOT")

import json
with open(utils.config.ROOT + '/data/lore.json', encoding='utf-8') as f:
    texts = json.load(f)

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


class GemHandler:
    EXIT = 0
    
    @staticmethod
    async def gems(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Tell them a little bit about gems, in the future it will give more options but for that I'll have to ask Gaia and Adrien about IW"""
        for message in texts["gems"]:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
            time.sleep(len(message)/140)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return GemHandler.EXIT
    
    handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex(re.compile(r'gems', re.IGNORECASE)), gems)],
        states={},
        fallbacks=[],
        map_to_parent={
            EXIT: EXIT
        }
    )

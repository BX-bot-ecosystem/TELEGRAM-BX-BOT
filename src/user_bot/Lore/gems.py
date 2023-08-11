import logging
import re
import time
import json
from dotenv import load_dotenv
import os

import utils
from utils import db, config

load_dotenv()
BOT_TOKEN = os.getenv("SAILORE_BX_BOT")

with open(config.ROOT + '/data/lore.json', encoding='utf-8') as f:
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
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class GemHandler:
    def __init__(self):
        self.EXIT = 0
        self.handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(re.compile(r'gems', re.IGNORECASE)), self.gems)],
            states={},
            fallbacks=[],
            map_to_parent={
                self.EXIT: self.EXIT
            }
        )
    
    async def gems(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Tell them a little bit about gems, in the future it will give more options but for that I'll have to ask Gaia and Adrien about IW"""
        for message in texts["gems"]:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
            time.sleep(len(message)/140)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return self.EXIT

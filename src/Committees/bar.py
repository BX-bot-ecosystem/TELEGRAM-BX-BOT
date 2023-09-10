import re

from . import base

from telegram import ReplyKeyboardMarkup, Update, InputFile
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)

import bx_utils

class Bar(base.Committee):
    def __init__(self):
        super().__init__(
            name=".9 Bar",
            home_handlers=[MessageHandler(filters.Regex(re.compile(r'menu', re.IGNORECASE)), self.menu)]
        )
        self.db_info = bx_utils.db.get_committee_info(self.name)

    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        
        await self.send_message(update, context, text="This is the current menu")

        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=InputFile(self.db_info["menu_id"]))
        return self.state.HOME

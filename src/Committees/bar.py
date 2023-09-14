import re
import os
import googleapiclient
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
import utils
class Bar(base.Committee):
    def __init__(self):
        super().__init__(
            name=".9 Bar",
            home_handlers=[MessageHandler(filters.Regex(re.compile(r'menu', re.IGNORECASE)), self.menu)]
        )
        self.db_info = bx_utils.db.get_committee_info(self.name)

    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        
        await self.send_message(update, context, text="This is the current menu")
        file_path = utils.config.ROOT + '/data/temp_files/menu.jpg'
        try:
            bx_utils.drive.download_committee_file(self.name, 'menu.jpg', file_path)
            with open(file_path, 'rb') as file:
                await context.bot.send_photo(chat_id=update.effective_chat.id,
                                             photo=file)
                os.remove(file_path)
        except googleapiclient.errors.HttpError:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="We are having problems at the moment, try again later")
        return self.state.HOME

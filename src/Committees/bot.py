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

class Bot(base.Committee):
    def __init__(self):
        super().__init__(
            "Bot"
        )
    
    async def apply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.send_message(update, context, "So you want to become part of the bot team?")
        
        return self.state.HOME

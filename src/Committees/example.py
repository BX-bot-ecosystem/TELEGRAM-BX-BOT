import time
import re
from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from utils import config, db

from Committees import base


class Example(base.Committee):
    def __init__(self):
        super().__init__(
            'example',
        )
    
import time
from typing import Dict
import json
import math
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackContext
)
import utils




def message_wait(message):
    return math.log(len(message), 10) - 1


class Members:
    def __init__(self):
        self.REPLY_KEYBOARD = [
            [InlineKeyboardButton("Yay", callback_data="Yay"), InlineKeyboardButton("Nay", callback_data="Nay")],
        ]
        self.MARKUP = InlineKeyboardMarkup(self.REPLY_KEYBOARD)
        
        self.INITIAL, self.LORE, self.CONTINUE = range(3)
        
        with open(utils.config.ROOT + '/data/lore.json', encoding='utf-8') as f:
            self.lore_texts = json.load(f)

        LORE_MEMBERS = [['Adrien', 'Eli', 'Giselle'],
                        ['Nic', 'Jeanne', 'Ryan'],
                        ['Ipop', 'Gaia', 'Angela']]

        self.LORE_MARKUP = InlineKeyboardMarkup(
            [[InlineKeyboardButton(name, callback_data=name) for name in members_list] for members_list in LORE_MEMBERS])

    async def intro(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Tell them a little bit about Sailore and allows them to learn about each of the members"""
        for i, message in enumerate(self.lore_texts["lore"]):
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
            time.sleep(message_wait(message))
            if i == len(self.lore_texts["lore"]) - 1:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=message,
                                               reply_markup=self.LORE_MARKUP)
            else:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        return self.LORE
    
    async def member(self, update: Update, context: CallbackContext) -> int:
        """General Sailore member info function"""
        query = update.callback_query
        await query.answer()
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(3)
        try:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=self.lore_texts[query.data])
        except KeyError:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Oh me matey, I don't know that pirate")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(0.5)
        await context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=self.MARKUP,
                                       text="Do you want to learn about any other pirate?")
        return self.CONTINUE

    async def more(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Ask about what other pirate do they wanna learn about"""
        query = update.callback_query
        await query.answer()
        if query.data == 'Yay':
            time.sleep(0.8)
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Which other pirate do you want to learn about me matey?",
                                           reply_markup=self.LORE_MARKUP)
            return self.LORE
        else:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
            time.sleep(0.6)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="What other stories can I tell you?")
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
            time.sleep(1.2)
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="We can talk about those shiny gems, the mighty Sail'ore or the different committees a pirate can join")
            return self.INITIAL
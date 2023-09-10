import enum

from telegram import ReplyKeyboardMarkup, Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from telegram.constants import ParseMode
import re
import time
import datetime
import math

import bx_utils
import utils

class Activity(enum.Enum):
    EXIT = -1
    HOME = 0
    SUB = 101
    UNSUB = 102
    BOARD = 103

class Committee:
    def __init__(self, name, home_handlers: list | None = None, extra_states: dict | None = None):
        self.name = name
        self.info = utils.config.committees_info[self.name]
        self.board_members = "\n".join([f'{self.info["board"][key]["role"]}: {key}' for key in self.info["board"]])
        self.board_keyboard = self.create_keyboard()
        self.reply_keyboard = [
            [InlineKeyboardButton("Yay", callback_data='Yay'), InlineKeyboardButton("Nay",callback_data='Nay')],
        ]
        self.MARKUP = InlineKeyboardMarkup(self.reply_keyboard)
        self.state = Activity.HOME
        if home_handlers is None:
            home_handlers = []
        if "messages" in self.info.keys():
            home_handlers.append(MessageHandler(filters.TEXT, self.generic))
            if not "help" in self.info["messages"].keys():
                self.info["messages"]["help"] = [f"You are in {self.name} bot section","Over here you can learn about their /board, their incoming /event or /sub to their communications"]
            if not "exit" in self.info["messages"].keys():
                self.info["messages"]["exit"] = ["See you again whenever you want to explore this great committee","After that, what do you want to talk about, we can talk about those shiny gems, the mighty Sail'ore or the different committees a pirate can join"]
            if not "predetermined" in self.info["messages"].keys():
                self.info["messages"]["predetermined"] = ["I didn't understand what you mean, you can always ask for /help"]
        self.states = {**{
            self.state.HOME: [
                           MessageHandler(
                               filters.Regex(re.compile(r'board', re.IGNORECASE)), self.board
                           ),
                           CommandHandler("sub", self.manage_sub),
                           CommandHandler("event", self.get_events),
                       ] + (home_handlers if home_handlers else []),
            self.state.BOARD: [
                CallbackQueryHandler(self.board_selection)
            ],
            self.state.SUB: [
                CallbackQueryHandler(self.sub)
            ],
        }, **(extra_states if extra_states else {})}
        self.handler = ConversationHandler(
            entry_points=[CommandHandler(self.info["command"][1:], self.intro)],
            states=self.states,
            fallbacks=[MessageHandler(filters.TEXT, self.generic)],
            map_to_parent={
                # Connection to the parent handler, note that its written EXIT: EXIT where both of these are equal to 0, that's why it leads to INITIAL which is also equal to 0
                self.state.EXIT: self.state.HOME
            }
        )

    async def intro(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Intro for the bar"""
        try:
            for line in self.info["messages"]["intro"]:
                await self.send_message(update, context, text=line)
        except KeyError:
            await self.send_message(update, context, text=f"Welcome to the {self.name} section of the Telegram Bot")
            await self.send_message(update, context, text="In here you can learn about our board, get the link to join our groupchat, find out about our next events and even subscribe to our notifications from this bot")
            await self.send_message(update, context, text="To exit this section of the bot just use the command /exit")
        return self.state.HOME
    async def generic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generic function that manages any extra commands added by the committees"""
        message = update.message.text
        message = message.strip('/')
        texts = self.info["messages"]
        keys = texts.keys()
        for key in keys:
            if re.match(key, message.lower()):
                text = texts[key]
                return_value = self.state.EXIT if key == 'exit' else self.state.HOME
                break
        else:
            text = texts["predetermined"]
            return_value = self.state.HOME
        for response in text:
            await self.send_message(update, context, response)
        return return_value
    def create_balanced_layout(self):
        names = [name for name in self.info["board"].keys() if 'message' in self.info["board"][name].keys()]
        total_members = len(names)
        ideal_group_size = math.isqrt(total_members)
        if names == []:
            return None
        remainder = total_members % ideal_group_size

        groups = [names[i:i + ideal_group_size] for i in range(0, total_members - remainder, ideal_group_size)]

        # Distribute the remaining members across the groups
        for i in range(remainder):
            groups[i].append(names[total_members - remainder + i])

        return groups
    def create_keyboard(self):
        layout = self.create_balanced_layout()
        if layout is None:
            return None
        keyboard = []
        for name_list in layout:
            keyboard_row = []
            for name in name_list:
                keyboard_row.append(InlineKeyboardButton(name, callback_data=name))
            keyboard.append(keyboard_row)
        keyboard.append([InlineKeyboardButton('Nay', callback_data='Nay')])
        return InlineKeyboardMarkup(keyboard)
    async def board_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data == 'Nay':
            await query.edit_message_text(text='Alright')
            return self.state.HOME
        message = f'{query.data}: "{self.info["board"][query.data]["message"]}"'
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(len(message) / 140)
        await query.edit_message_text(text=message)
        await self.send_message(update, context, text='Do you want to learn more about any other members?', reply_markup=self.board_keyboard)
    async def board(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Introduces the board"""
        await self.send_message(update, context, text=f"Voici the members of the {self.name} board:\n" + self.board_members)
        reply_markup = self.board_keyboard
        if reply_markup is None:
            return self.state.HOME
        await self.send_message(update, context, text='Do you want to learn more about any of these members?', reply_markup=self.board_keyboard)
        return self.state.BOARD
    async def sub(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data[0] == 'T' and query.data[1] == 'T':
            user_info = bx_utils.config.r.hgetall(bx_utils.db.user_to_key(update.effective_user))
            sub_list = bx_utils.db.db_to_list(user_info['subs'])
            sub_list.append(self.name)
            subs = bx_utils.db.list_to_db(sub_list)
            user_info['subs'] = subs
            bx_utils.config.r.hset(bx_utils.db.user_to_key(update.effective_user), mapping=user_info)
            await self.send_message(update, context,
                                    text=f'You have been subscribed to {self.name}')
            await self.send_message(update, context,
                                    text='In order to receive communications interact at least once with t.me/SailoreParrotBot')
            return self.state.HOME
        elif query.data[0] == 'T' and query.data[1] == 'F':
            user_info = bx_utils.config.r.hgetall(bx_utils.db.user_to_key(update.effective_user))
            sub_list = bx_utils.db.db_to_list(user_info['subs'])
            sub_list.remove(self.name)
            subs = bx_utils.db.list_to_db(sub_list)
            user_info['subs'] = subs
            bx_utils.config.r.hset(bx_utils.db.user_to_key(update.effective_user), mapping=user_info)
            await self.send_message(update, context, text=f'You have been unsubscribed to {self.name}')
            return self.state.HOME
        await query.edit_message_text(text='Alright')
        return self.state.HOME
    async def manage_sub(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Checks if the user is subscribed and allows it to toogle it"""
        user_info = bx_utils.db.r.hgetall(bx_utils.db.user_to_key(update.effective_user))
        sub_list = bx_utils.db.db_to_list(user_info["subs"])
        sub_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Yay', callback_data='TT'),
                                            InlineKeyboardButton('Nay', callback_data='FT')]])
        unsub_markup = InlineKeyboardMarkup([[InlineKeyboardButton('Yay', callback_data='TF'),
                                            InlineKeyboardButton('Nay', callback_data='FF')]])
        if self.name in sub_list:
            await self.send_message(update, context, text='It seems like you are already subscribed to this committee')
            await self.send_message(update, context, text='This means that you will receive their communications through our associated bot @SailoreParrotBot')
            await self.send_message(update, context, text='Do you wish to unsubscribe?', reply_markup=unsub_markup)
            return self.state.SUB
        else:
            await self.send_message(update, context, text='It seems like you are not subscribed to this committee')
            await self.send_message(update, context, text='Doing so will mean that you will receive their communications through our associated bot @SailoreParrotBot')
            await self.send_message(update, context, text='Do you wish to subscribe?', reply_markup=sub_markup)
            return self.state.SUB
    async def get_events(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        time_now = datetime.datetime.now()
        two_weeks_from_now = time_now + datetime.timedelta(days = 14)
        time_max = two_weeks_from_now.isoformat() + 'Z'
        events = bx_utils.gc.get_committee_events(self.name, time_max=time_max)
        event_descriptions = []
        for item in events:
            event_descriptions.append(bx_utils.gc.event_presentation_from_api(item))
        message = '\n -------------------------------------- \n'.join(event_descriptions)
        if len(event_descriptions) == 0:
            await self.send_message(update, context, text=f"{self.name} has no events planned in the near future")
        else:
            await self.send_message(update, context, text="The events already planned are:")
            await self.send_message(update, context, text=message, parse_mode=ParseMode.HTML)
        return self.state.HOME

    @staticmethod
    async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text, parse_mode=None, reply_markup=None):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(len(text)/140)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=parse_mode, reply_markup=reply_markup) 

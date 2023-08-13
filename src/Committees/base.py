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
        self.EXIT, self.HOME, self.SUB, self.UNSUB, self.BOARD = range(5)
        if home_handlers is None:
            home_handlers = []
        if "messages" in self.info.keys():
            if "info" in self.info["messages"].keys():
                home_handlers.append(CommandHandler("info", self.about))
            if "groupchat" in self.info["messages"].keys():
                home_handlers.append(CommandHandler("groupchat", self.groupchat))
        self.states = {**{
            self.HOME: [
                           MessageHandler(
                               filters.Regex(re.compile(r'board', re.IGNORECASE)), self.board
                           ),
                           CommandHandler("sub", self.manage_sub),
                           CommandHandler("event", self.get_events),
                           CommandHandler("exit", self.exit),
                           CommandHandler("help", self.help)
                       ] + (home_handlers if home_handlers else []),
            self.BOARD: [
                CallbackQueryHandler(self.board_selection)
            ],
            self.SUB: [
                CallbackQueryHandler(self.sub)
            ],
        }, **(extra_states if extra_states else {})}
        self.handler = ConversationHandler(
            entry_points=[CommandHandler(self.info["command"][1:], self.intro)],
            states=self.states,
            fallbacks=[MessageHandler(filters.TEXT, self.predetermined)],
            map_to_parent={
                # Connection to the parent handler, note that its written EXIT: EXIT where both of these are equal to 0, that's why it leads to INITIAL which is also equal to 0
                self.EXIT: self.EXIT
            }
        )

    async def intro(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Intro for the bar"""
        try:
            for line in self.info["messages"]["intro"]:
                await self.send_message(update, context, text=line)
        except KeyError:
            await self.send_message(update, context, text=f"Welcome to the {self.name} section of the Telegram Bot")
            await self.send_message(update, context, text="In here you can learn about our board, get the link to join our groupchat, find out about our next events and even subscribe to our notifications from this bot")
            await self.send_message(update, context, text="To exit this section of the bot just use the command /exit")
        return self.HOME

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
            return self.HOME
        message = f'{query.data}: "{self.info["board"][query.data]["message"]}"'
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(len(message) / 140)
        await query.edit_message_text(text=message)
        await self.send_message(update, context, text='Do you want to learn more about any other members?', reply_markup=self.board_keyboard)

    async def board(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Introduces the board"""
        await self.send_message(update, context, text=f"Voici the members of the {self.name} board:\n" + self.board_members)
        reply_markup = self.board_keyboard
        if reply_markup is None:
            return self.HOME
        await self.send_message(update, context, text='Do you want to learn more about any of these members?', reply_markup=self.board_keyboard)
        return self.BOARD


    async def exit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Exit of the committee section"""
        try:
            for line in self.info["messages"]["intro.py"]:
                await self.send_message(update, context, text=line)
        except KeyError:
            await self.send_message(update, context, text="See you again whenever you want to explore this great committee")
            await self.send_message(update, context, text="After that, what do you want to talk about, we can talk about those shiny gems, the mighty Sail'ore or the different committees a pirate can join")
            return self.EXIT

    async def sub(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.callback_query
        await query.answer()
        if query.data == 'Yay':
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
            return self.HOME
        if query.data == 'Nay':
            user_info = bx_utils.config.r.hgetall(bx_utils.db.user_to_key(update.effective_user))
            sub_list = bx_utils.db.db_to_list(user_info['subs'])
            sub_list.remove(self.name)
            subs = bx_utils.db.list_to_db(sub_list)
            user_info['subs'] = subs
            bx_utils.config.r.hset(bx_utils.db.user_to_key(update.effective_user), mapping=user_info)
            await self.send_message(update, context, text=f'You have been unsubscribed to {self.name}')
            return self.HOME

    async def manage_sub(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Checks if the user is subscribed and allows it to toogle it"""
        user_info = bx_utils.db.r.hgetall(bx_utils.db.user_to_key(update.effective_user))
        sub_list = bx_utils.db.db_to_list(user_info["subs"])
        if self.name in sub_list:
            await self.send_message(update, context, text='It seems like you are already subscribed to this committee')
            await self.send_message(update, context, text='This means that you will receive their communications through our associated bot @SailoreParrotBot')
            await self.send_message(update, context, text='Do you wish to unsubscribe?', reply_markup=self.MARKUP)
            return self.UNSUB
        else:
            await self.send_message(update, context, text='It seems like you are not subscribed to this committee')
            await self.send_message(update, context, text='Doing so will mean that you will receive their communications through our associated bot @SailoreParrotBot')
            await self.send_message(update, context, text='Do you wish to subscribe?', reply_markup=self.MARKUP)
            return self.SUB

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
        return self.HOME

    async def about(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        for message in self.info["messages"]["info"]:
            await self.send_message(update, context, message)
        return self.HOME

    async def groupchat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        for message in self.info["messages"]["groupchat"]:
            await self.send_message(update, context, message)
        return self.HOME

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            for message in self.info["messages"]["help"]:
                await self.send_message(update, context, message)
        except KeyError:
            await self.send_message(update, context, f"You are in {self.name} bot section")
            await self.send_message(update, context, f"Over here you can learn about their /board, their incoming /event or /sub to their communications")
        return self.HOME

    async def predetermined(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            for message in self.info["messages"]["predetermined"]:
                await self.send_message(update, context, message)
        except KeyError:
            await self.send_message(update, context, "I didn't understand what you mean, you can always ask for /help")

    @staticmethod
    async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text, parse_mode=None, reply_markup=None):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(len(text)/140)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, parse_mode=parse_mode, reply_markup=reply_markup) 

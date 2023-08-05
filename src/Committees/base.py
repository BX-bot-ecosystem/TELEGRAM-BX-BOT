from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode
import re
import time
import datetime


import utils


class Committee:
    def __init__(self, name, home_handlers: list | None = None, extra_states: dict | None = None):
        self.name = name
        self.info = utils.config.committees_info[self.name]
        self.board_members = "\n".join([key for key in self.info["board"]])
        
        self.reply_keyboard = [
            ["Yay", "Nay"],
        ]
        self.MARKUP = ReplyKeyboardMarkup(self.reply_keyboard, one_time_keyboard=True)
        self.EXIT, self.HOME, self.SUB, self.UNSUB = range(4)
        self.states = {**{
                self.HOME: [
                    MessageHandler(
                        filters.Regex(re.compile(r'board', re.IGNORECASE)), self.board
                    ),
                    CommandHandler("sub", self.manage_sub),
                    CommandHandler("event", self.get_events),
                    CommandHandler("exit", self.exit)
                ] + (home_handlers if home_handlers else []),
                self.SUB: [
                    MessageHandler(
                        filters.Regex(re.compile(r'yay', re.IGNORECASE)), self.sub
                    )
                ],
                self.UNSUB: [
                    MessageHandler(
                        filters.Regex(re.compile(r'yay', re.IGNORECASE)), self.unsub
                    )
                ]
            }, **(extra_states if extra_states else {})}
        self.handler = ConversationHandler(
            entry_points=[CommandHandler(self.info["code"], self.intro)],
            states=self.states,
            fallbacks=[MessageHandler(filters.TEXT, self.intro)],
            map_to_parent={
                # Connection to the parent handler, note that its written EXIT: EXIT where both of these are equal to 0, that's why it leads to INITIAL which is also equal to 0
                self.EXIT: self.EXIT
            }
        )
    
    async def intro(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Intro for the bar"""
        await self.send_message(update, context, text=f"Welcome to the {self.name} section of the Telegram Bot")
        await self.send_message(update, context, text="In here you can learn about our board, get the link to join our groupchat, find out about our next events and even subscribe to our notifications from this bot")
        await self.send_message(update, context, text="To exit this section of the bot just use the command /exit")
        return self.HOME
    
    async def board(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Introduces the board"""
        await self.send_message(update, context, text=f"Voici the members of the {self.name} board:\n" + self.board_members)
        return self.HOME

    async def exit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Exit of the committee section"""
        await self.send_message(update, context, text="See you again whenever you want to explore this great committee")
        await self.send_message(update, context, text="After that, what do you want to talk about, we can talk about those shiny gems, the mighty Sail'ore or the different committees a pirate can join")
        return self.EXIT

    async def sub(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_info = utils.config.r.hgetall(utils.db.user_to_key(update.effective_user))
        sub_list = utils.db.db_to_list(user_info['subs'])
        sub_list.append(self.name)
        subs = utils.db.list_to_db(sub_list)
        user_info['subs'] = subs
        utils.config.r.hset(utils.db.user_to_key(update.effective_user), mapping=user_info)
        await self.send_message(update, context,
                                       text=f'You have been subscribed to {self.name}')
        await self.send_message(update, context,
                                       text='In order to receive communications interact at least once with t.me/SailoreParrotBot')
        return self.HOME

    async def unsub(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_info = utils.config.r.hgetall(utils.db.user_to_key(update.effective_user))
        sub_list = utils.db.db_to_list(user_info['subs'])
        sub_list.remove(self.name)
        subs = utils.db.list_to_db(sub_list)
        user_info['subs'] = subs
        utils.config.r.hset(utils.db.user_to_key(update.effective_user), mapping=user_info)
        await self.send_message(update, context, text=f'You have been unsubscribed to {self.name}')
        return self.HOME
    
    async def manage_sub(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Checks if the user is subscribed and allows it to toogle it"""
        user_info = utils.db.r.hgetall(utils.db.user_to_key(update.effective_user))
        sub_list = utils.db.db_to_list(user_info["subs"])
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
        events = utils.gc.get_committee_events(self.name, time_max=time_max)
        event_descriptions = []
        for item in events:
            event_descriptions.append(utils.gc.event_presentation_from_api(item))
        message = '\n -------------------------------------- \n'.join(event_descriptions)
        if len(event_descriptions) == 0:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f"{self.name} has no events planned in the near future")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="The events already planned are:")
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=message,
                                           parse_mode=ParseMode.HTML)
        return self.HOME
    
    @staticmethod
    async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text, reply_markup=None):
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(len(text)/140)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup) 

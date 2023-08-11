import re
import time
from utils import config, db, gc
import datetime
from telegram import ReplyKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from Committees import base
r = config.r

class Bar(base.Committee):
    def __init__(self):
        super().__init__(
            name=".9 Bar"
        )

class Bar_old:
    def __init__(self):
        self.REPLY_KEYBOARD = [
            ["Yay", "Nay"],
        ]
        self.MARKUP = ReplyKeyboardMarkup(self.REPLY_KEYBOARD, one_time_keyboard=True)
        self.committee_name = ".9 Bar"
        self.BOARD_MEMBERS = "\n".join(["Prez: Carlos", "VPrez: Maxime", "Stock: Gabin", "Comms: Alix", "Events: Anahí", "Sked: Johanna", "Bartenders: Arturo, Antoine"])
        self.EXIT, self.HOME, self.SUB, self.UNSUB = range(4)

        self.handler = ConversationHandler(
            entry_points=[CommandHandler("bar", self.bar_intro)],
            states={
                self.HOME: [
                    MessageHandler(
                        filters.Regex(re.compile(r'board', re.IGNORECASE)), self.bar_board
                    ),
                    CommandHandler("sub", self.manage_sub),
                    CommandHandler("event", self.get_events),
                    CommandHandler("exit", self.exit)
                ],
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
            },
            fallbacks=[MessageHandler(filters.TEXT, self.bar_intro)],
            map_to_parent={
                # Connection to the parent handler, note that its written EXIT: EXIT where both of these are equal to 0, that's why it leads to INITIAL which is also equal to 0
                self.EXIT: self.EXIT
            }
        )

    async def bar_intro(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Intro for the bar"""
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(1.2)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Welcome to the .9bar section of the Telegram Bot")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(1.2)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="In here you can learn about our board, get the link to join our groupchat, find out about our next events and even subscribe to our notifications from this bot")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(1.2)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="To exit this section of the bot just use the command /exit")
        return self.HOME
    
    async def bar_board(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Introduces the bar board"""
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(1.2)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="The .9 bar is excellent we have lots of motivated people here")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(1.2)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="The members of the board are the following:\n" + self.BOARD_MEMBERS)
        return self.HOME
    
    async def exit(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Exit of the committee section"""
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(1.2)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="See you again whenever you want to explore this great committee")
    
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(2)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="After that, what do you want to talk about, we can talk about those shiny gems, the mighty Sail'ore or the different committees a pirate can join")
        return self.EXIT
    
    async def manage_sub(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Checks if the user is subscribed and allows it to toogle it"""
        user_info = r.hgetall(db.user_to_key(update.effective_user))
        sub_list = db.db_to_list(user_info["subs"])
        if self.committee_name in sub_list:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='It seems like you are already subscribed to this committee')
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='This means that you will receive their communications through our associated bot @SailoreParrotBot')
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='Do you wish to unsubscribe?',
                                           reply_markup=self.MARKUP)
            return self.UNSUB

        else:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='It seems like you are not subscribed to this committee')
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='Doing so will mean that you will receive their communications through our associated bot @SailoreParrotBot')
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text='Do you wish to subscribe?',
                                           reply_markup=self.MARKUP)
            return self.SUB

    async def sub(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_info = r.hgetall(db.user_to_key(update.effective_user))
        sub_list = db.db_to_list(user_info['subs'])
        sub_list.append(self.committee_name)
        subs = db.list_to_db(sub_list)
        user_info['subs'] = subs
        r.hset(db.user_to_key(update.effective_user), mapping=user_info)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f'You have been subscribed to {self.committee_name}')
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='In order to receive communications interact at least once with t.me/SailoreParrotBot')
        return self.HOME

    async def unsub(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_info = r.hgetall(db.user_to_key(update.effective_user))
        sub_list = db.db_to_list(user_info['subs'])
        sub_list.remove(self.committee_name)
        subs = db.list_to_db(sub_list)
        user_info['subs'] = subs
        r.hset(db.user_to_key(update.effective_user), mapping=user_info)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f'You have been unsubscribed to {self.committee_name}')
        return self.HOME

    async def get_events(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        time_now = datetime.datetime.now()
        two_weeks_from_now = time_now + datetime.timedelta(days = 14)
        time_max = two_weeks_from_now.isoformat() + 'Z'
        events = event.get_committee_events(self.committee_name, time_max=time_max)
        event_descriptions = []
        for item in events:
            event_descriptions.append(event.event_presentation_from_api(item))
        message = '\n -------------------------------------- \n'.join(event_descriptions)
        if len(event_descriptions) == 0:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=f"{self.committee_name} has no events planned in the near future")
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="The events already planned are:")
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text=message,
                                           parse_mode=ParseMode.HTML)
        return self.HOME

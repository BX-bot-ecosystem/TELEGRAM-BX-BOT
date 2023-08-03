import logging
import json
import random
import string
import datetime
import telegram.error
import enum

import telegram_bot_calendar.detailed
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from utils import db, config, passwords, event

from telegram import __version__ as TG_VER
try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    CallbackContext
)

with open('../credentials.json') as f:
    tokens = json.load(f)
    committees_token = tokens["SailoreCommitteesBot"]
    parrot_token = tokens["SailoreParrotBot"]
    sailore_token = tokens["SailoreBXBot"]

with open('../data/Committees/committees.json') as f:
    committees = json.load(f)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

class Activity(enum.Enum):
    HOME = 1
    LOGIN = 2
    VERIFICATION = 3
    HUB = 4
    MESSAGE = 5
    ACCESS = 6
    RIGHTS = 7
    APPLY_ROLE = 8
    CONFIRMATION_RIGHTS = 9
    EVENT = 10
    DATE = 11
    START_TIME = 12
    END_TIME = 13
    NAME = 14
    SUMMARY = 15
    CONFIRMATION_EVENT = 16

def create_time_keyboard():
    keyboard = []
    hours = [str(i).zfill(2) for i in range(0, 24)]

    for i in range(0, 24, 6):
        row = []
        for j in range(6):
            hour = hours[i + j]
            row.append(InlineKeyboardButton(hour, callback_data=hour))
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)

def create_minutes_keyboard(hour):
    keyboard = [[]]
    times = [hour + ':00', hour + ':15', hour + ':30', hour + ':45']
    for time in times:
        keyboard[0].append(InlineKeyboardButton(time, callback_data=time))
    return InlineKeyboardMarkup(keyboard)

class Right_changer:
    class State(enum.Enum):
        USER = 1
        ROLE = 2
        CONFIRMATION = 3
        MORE = 4
    def __init__(self, user_rights):
        self.user_rights = user_rights
        self.active_user = [user for user in user_rights.keys() if user_rights[user] == 'Prez'][0]
        self.keyboard = [[]]
        self.state = self.State.USER
        self.new_user_rights = user_rights
        self.params = {}

    def build(self):
        if self.state == self.State.USER:
            self._build_users()
        if self.state == self.State.ROLE:
            self._build_role()
        if self.state == self.State.CONFIRMATION:
            self._build_confirmation()
        if self.state == self.State.MORE:
            self._build_more()

    def process(self, call_data):
        # callback = user_role_confirmation_more
        params = call_data.split('_')
        params = dict(zip(['user', 'role', 'confirmation', 'more'][:len(params)], params))
        self.params = params
        if len(params) == 1:
            self.state = self.State.ROLE
            return False, 'role', None
        elif len(params) == 2:
            self.state = self.State.CONFIRMATION
            return False, 'confirm', None
        elif len(params) == 3:
            if params['confirmation'] == 'yay':
                self.new_user_rights[self.params['user']] = self.params['role']
                if self.params['role'] == 'Prez':
                    self.new_user_rights[self.active_user] = 'Admin'
                self.state = self.State.MORE
                return True, 'more', self.new_user_rights
            self.state = self.State.MORE
            return False, 'more', None
        elif len(params) == 4:
            if params['more'] == 'yay':
                self.user_rights = self.new_user_rights
                self.state = self.State.USER
                return True, 'user', None
            return False, 'user', None

    def _build_users(self):
        user_list = [[user] for user in self.user_rights.keys() if user != self.active_user]
        self.keyboard = self._build_keyboard(user_list)

    def _build_role(self):
        roles = [['Prez'], ['Admin'], ['Comms'], ['Events'], ['None']]
        self.keyboard = self._build_keyboard(roles)

    def _build_confirmation(self):
        confirmation = [['yay', 'nay']]
        self.keyboard = self._build_keyboard(confirmation)

    def _build_more(self):
        more = [['yay', 'nay']]
        self.keyboard = self._build_keyboard(more)

    def _build_keyboard(self, elements):
        keyboard = []
        for i, row in enumerate(elements):
            keyboard.append([])
            for element in row:
                callback = self._build_callback(element)
                keyboard[i].append(InlineKeyboardButton(element, callback_data=callback))
        return InlineKeyboardMarkup(keyboard)

    def _build_callback(self, element):
        if self.state == self.State.USER:
            return element
        if self.state == self.State.ROLE:
            return f'{self.params["user"]}_{element}'
        if self.state == self.State.CONFIRMATION:
            return f'{self.params["user"]}_{self.params["role"]}_{element}'
        if self.state == self.State.MORE:
            return f'{self.params["user"]}_{self.params["role"]}_{self.params["confirmation"]}_{element}'

class Event_handler:
    def __init__(self, active_committee):
        self.state = Activity.EVENT
        self.active_committee = active_committee
        self.date = ''
        self.start_time = ''
        self.end_time = ''
        self.name = ''
        self.user_rights = ''
        self.description = ''
        self.event_description = ''
        self.time_markup = create_time_keyboard()
        self.event_handler = ConversationHandler(
            entry_points=[CommandHandler("event", self.event)],
            states={
                self.state.EVENT: [CallbackQueryHandler(self.event)],
                self.state.DATE: [CallbackQueryHandler(self.date_selection)],
                self.state.START_TIME: [CallbackQueryHandler(self.select_start)],
                self.state.END_TIME: [CallbackQueryHandler(self.select_end)],
                self.state.NAME: [MessageHandler(filters.TEXT, self.naming)],
                self.state.SUMMARY: [MessageHandler(filters.TEXT, self.summary)],
                self.state.CONFIRMATION_EVENT: [CallbackQueryHandler(self.confirmation)]
            },
            fallbacks=[MessageHandler(filters.TEXT, self.back)],
            map_to_parent={
                self.state.HUB: self.state.HUB,
            }
        )
    async def back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="You are back to the hub")
        return self.state.HUB

    async def event(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.user_rights == 'Comms':
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="You don't have access rights for this functionality")
            return self.state.HUB
        Calendar_Object = DetailedTelegramCalendar()
        Calendar_Object.first_step = 'm'
        calendar, step = Calendar_Object.build()

        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="When do you want to create an event?",
                                       reply_markup=calendar)
        return self.state.DATE

    async def date_selection(self, update: Update, context: CallbackContext):
        query = update.callback_query
        data = query.data

        result, key, step = DetailedTelegramCalendar().process(data)

        if not result and key:
            await query.edit_message_text(f"Select {LSTEP[step]}", reply_markup=key)
            context.user_data["step"] = step  # Update the step in user_data
            return self.state.DATE
        elif result:
            await query.edit_message_text(f"You selected the date {result}")
            self.date = result
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="What time does your event start?",
                                           reply_markup=self.time_markup)
            return self.state.START_TIME

    async def select_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        response = update.message.text

        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="What time does it end?",
                                       reply_markup=self.time_markup)
        return self.state.END_TIME

    async def select_end(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        response = update.message.text
        if len(response.split()) != 2:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Incorrect format, when inputting the hour use the format: hh mm")
            return self.state.END_TIME

        self.end_time = response.split()
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Give it a name")
        return self.state.NAME

    async def naming(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.name = update.message.text
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Give a brief description of your event")
        return self.state.SUMMARY

    async def summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.description = update.message.text
        formatted_date = event.format_date(self.date)
        self.event_description = f"{self.active_committee} is organizing <b>{self.name}</b> on the {formatted_date}\n {self.description}"
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"Current Event:\n {self.event_description}",
                                       reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('yay', callback_data='True'), InlineKeyboardButton('nay', callback_data='False')]]),
                                       parse_mode=ParseMode.HTML)
        return self.state.CONFIRMATION_EVENT

    async def confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        if query.data == 'False':
            await query.edit_message_text(text="Event upload cancelled")
            return self.state.HUB
        await query.edit_message_text(text=f"The event has been uploaded to the google calendar, users will be able to see it on your committee part of SailoreBXBot two weeks prior to the event")
        event.create_event(self.date, self.start_time, self.end_time, self.active_committee, self.description)
        return self.state.HUB


class Access_handler:
    def __init__(self, active_committee):
        self.active_committee = active_committee
        access_granted = db.get_committee_access(self.active_committee)
        keys = ['user:' + user_id for user_id in access_granted.keys()]
        admins_info = db.get_users_info(keys)
        self.admins_rights = {admin['name']: access_granted[admin['id']] for admin in admins_info}
        self.admins_ids = {admin['name']: admin['id'] for admin in admins_info}
        self.state = Activity.ACCESS
        self.access_list = []
        self.user_rights = None
        self.right_changer = Right_changer(self.admins_rights)
        self.access_handler=ConversationHandler(
            entry_points=[CommandHandler("access", self.access)],
            states={
                self.state.ACCESS: [
                    CommandHandler("password", self.password),
                    CommandHandler("rights", self.rights),
                    CommandHandler("back", self.back)
                ],
                self.state.RIGHTS: [
                    CallbackQueryHandler(self.chose_role)
                ],
            },
            fallbacks=[MessageHandler(filters.TEXT, self.access)],
            map_to_parent={
                self.state.HUB: self.state.HUB
            }
        )

    async def back(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="You are back to the hub")
        return self.state.HUB
    async def access(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not self.user_rights == 'Prez':
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="You don't have access rights for this functionality")
            return self.state.HUB
        roles = ["Prez: All functionalities + access management", "Admin: All functionalities", "Comms: Message functionality", "Events: Events functionality"]
        current_admins = [f"{key}: {value}" for key, value in self.admins_rights.items()]
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Inside any committee hub the following roles are allowed: \n" + '\n'.join(roles))
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="The current users with access are: \n" + '\n'.join(current_admins))
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Do you want to generate a one-time /password to register a new user or change the current /rights (you can also go /back to the hub)")
        return self.state.ACCESS
    async def password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        new_password=self.active_committee + ':' + ''.join(random.choices(string.digits + string.ascii_letters, k=10))
        db.add_one_time_pass(new_password, self.active_committee)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"The password generated is <b>{new_password}</b>, the default rights are admin for new users",
                                       parse_mode=ParseMode.HTML)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"This password only has one use, send it to the person you want to give access")
        return self.state.HUB
    async def rights(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.right_changer = Right_changer(self.admins_rights)
        self.right_changer.build()
        keyboard = self.right_changer.keyboard
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="Who's right do you want to change?",
                                       reply_markup=keyboard)
        return self.state.RIGHTS
    async def chose_role(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Parses the CallbackQuery and updates the message text."""
        query = update.callback_query
        await query.answer()
        data = query.data
        result, state, rights = self.right_changer.process(data)
        if result and state=='more':
            #save the changes
            self.admins_rights = self.right_changer.new_user_rights
        if not result and state=='user':
            if 'None' in self.admins_rights.values():
                users_to_eliminate = [user for user in self.admins_rights.keys() if self.admins_rights[user] == 'None']
                for user in users_to_eliminate:
                    del self.admins_rights[user]
                    committee_command = [key for key in committees.keys() if committees[key] == self.active_committee][0]
                    db.eliminate_access_rights(self.admins_ids[user], self.active_committee, committee_command)
            new_rights = {self.admins_ids[admin]: self.admins_rights[admin] for admin in self.admins_rights.keys()}
            db.change_committee_access(self.active_committee, new_rights)
            await query.edit_message_text(text="The rights have been updated accordingly")
            return self.state.HUB
        self.right_changer.build()
        keyboard = self.right_changer.keyboard
        params = data.split('_')
        message = {'user': "Who's right do you want to change?", 'role': "Which role do you want to apply? \n (Selecting Prez will change your role to Admin)", 'confirm': f"Confirm the change of {params[0]} to {params[-1]}", 'more': "Do you want to make any other changes"}
        await query.edit_message_text(text=message[state], reply_markup=keyboard)
        return self.state.RIGHTS

class Committee_hub:
    def __init__(self, active_committee):
        self.active_committee = active_committee
        self.state = Activity.HUB
        self.access_handler = Access_handler(active_committee)
        self.event_handler = Event_handler(active_committee)
        self.user_rights = None
        hub_handlers = [CommandHandler("subs", self.give_subs),
                        CommandHandler("message", self.message),
                        self.event_handler.event_handler,
                        self.access_handler.access_handler,
                        CommandHandler("logout", self.logout),
                        MessageHandler(filters.TEXT, self.hub)]
        self.committee_handler=ConversationHandler(
            entry_points=hub_handlers,
            states={
                self.state.HUB: hub_handlers,
                self.state.MESSAGE: [MessageHandler(filters.TEXT, self.parrot)],
            },
            fallbacks=[MessageHandler(filters.TEXT, self.hub)],
            map_to_parent={
                self.state.HOME: self.state.HOME
            }
        )
    async def hub(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.user_rights = db.get_committee_access(self.active_committee)[str(update.effective_user.id)]
        self.access_handler.user_rights = self.user_rights
        self.event_handler.user_rights = self.user_rights
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text=f"You are logged into {self.active_committee} as {self.user_rights}")
        if self.user_rights == 'Prez':
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="From here you can check your /subs, send them a /message, upload an /event to the google calendar or manage the /access to this committee hub")
        elif self.user_rights == 'Admin':
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="From here you can check your /subs, send them a /message or upload an /event to the google calendar")
        elif self.user_rights == 'Comms':
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="From here you can check your /subs or send them a /message")
        elif self.user_rights == 'Events':
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="From here you can check your /subs or upload an /event to the google calendar")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="If you want to access other committee, then /logout")
        return self.state.HUB
    async def give_subs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keys = db.subs_of_committee(self.active_committee)
        users_info = db.get_users_info(keys)
        names = [user["fullname"] for user in users_info]

        names.insert(0, '')
        name_list = '\n - '.join(names)
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text=f"Your committee has a total of {len(names) - 1} subs")
        if len(names) > 1:
            await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="This is the full list:" + name_list)
        return self.state.HUB
    async def message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.user_rights == 'Events':
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="You don't have access rights for this functionality")
            return self.state.HUB
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="What message do you wish to send to your subscriptors?")
        return self.state.MESSAGE
    async def parrot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message = update.message.text
        keys = db.subs_of_committee(self.active_committee)
        users_info = db.get_users_info(keys)
        parrot_bot = Bot(parrot_token)
        sailore_bot = Bot(sailore_token)
        counter = 0
        for user in users_info:
            try:
                await parrot_bot.send_message(chat_id=user['id'],
                                               text=f'Hello {user["name"]}, this is a communication from {self.active_committee}:')
                await parrot_bot.send_message(chat_id=user['id'], text=message)
            except telegram.error.BadRequest:
                counter += 1
                await sailore_bot.send_message(chat_id=user['id'],
                    text=f"""Hello {user['name']}, a communication from one of your subscriptions was just sent to you but you didn't receive it as you haven't signed in into t.me/SailoreParrotBot""")
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="Successfully echoed your message")
        if counter > 0:
            await context.bot.send_message(chat_id=update.effective_user.id,
                                           text=f"We also notified {counter} of your users which didn't sign into @SailoreParrotBot")
        return self.state.HUB
    async def event(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if self.user_rights == 'Comms':
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="You don't have access rights for this functionality")
            return self.state.HUB
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Functionality to be implemented")
    async def logout(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="Successful logout")
        return self.state.HOME

class Committees_Login:
    def __init__(self):
        self.active_committee = ''
        self.state = Activity.HOME
        self.committee_hub = ''
        self.access_list = []
        self.login_handler=ConversationHandler(
            entry_points=[MessageHandler(filters.TEXT, self.start)],
            states={
                self.state.HOME: [
                    MessageHandler(filters.TEXT, self.start)
                ],
                self.state.LOGIN: [
                    CommandHandler("password", self.password_access),
                    MessageHandler(filters.TEXT, self.login)
                ],
                self.state.VERIFICATION: [
                    MessageHandler(filters.TEXT, self.verify_password)
                ],
                self.state.HUB: [

                ]
            },
            fallbacks=[MessageHandler(filters.TEXT, self.start)]
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        info = db.get_user_info(update.effective_user)
        rights = info["rights"]
        access_list = db.db_to_list(rights)
        message_list = db.list_to_telegram(access_list)
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="This bot is for committees to manage their bot sections")
        if len(access_list) == 0:
            await context.bot.send_message(chat_id=update.effective_user.id,
                                           text="Right now you don't have access to any committees")
        else:
            await context.bot.send_message(chat_id=update.effective_user.id,
                                           text="Right now you have access to the following committees \n" + message_list)
            self.access_list = access_list
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="To gain admin access to a new committee ask your committee head for a one time password")
        await context.bot.send_message(chat_id=update.effective_user.id,
                                       text="Once generated use the command /password to gain access")
        return self.state.LOGIN
    async def login(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        committee = update.message.text
        if committee in self.access_list:
            self.active_committee = committees[committee]
            await context.bot.send_message(chat_id=update.effective_user.id,
                                           text=f"You have successfully logged in")
            self.update_hub()
            await self.committee_hub.hub(update, context)
            return self.state.HUB
        else:
            await context.bot.send_message(chat_id=update.effective_user.id,
                                           text="That is not a valid choice, either you don't have access or it doesn't exist")
            return self.state.HOME

    def update_hub(self):
        """
        Update the info about the committee name in all handlers
        """
        self.committee_hub = Committee_hub(self.active_committee)
        self.login_handler.states[self.state.HUB] = [self.committee_hub.committee_handler]
    async def password_access(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="What is your one time password?")
        return self.state.VERIFICATION

    async def verify_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        password = update.message.text
        committee_name = password.split(':')[0]
        try:
            committee_command = [key for key in committees.keys() if committees[key] == committee_name][0]
        except IndexError:
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Error: either you entered an incorrect password or one has not been generated")
            return self.state.HOME
        if not db.use_one_time_pass(password, committee_name):
            await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Error: either you entered an incorrect password or one has not been generated")
            return self.state.HOME
        result = db.add_access_rights(update.effective_user, committee_name, committee_command)
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                           text="Your rights have been successfully updated")
        return self.state.HOME

def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(committees_token).build()
    committees_hub = Committees_Login()
    application.add_handler(committees_hub.login_handler)

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
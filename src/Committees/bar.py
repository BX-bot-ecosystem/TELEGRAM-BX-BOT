import enum
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
    CallbackContext,
)

import bx_utils
import utils
BAR_ID = -4050559023
class Bar(base.Committee):
    class Activity(enum.Enum):
        EXIT = -1
        HOME = 0
        DRINKS = 10
        ORDER = 11
        SUB = 101
        UNSUB = 102
        BOARD = 103
    def __init__(self):
        self.state = self.Activity.HOME
        super().__init__(
            name=".9 Bar",
            home_handlers=[MessageHandler(filters.Regex(re.compile(r'order', re.IGNORECASE)), self.order),
                           CommandHandler("order", self.order),
                           MessageHandler(filters.Regex(re.compile(r'order', re.IGNORECASE)), self.menu)],
            extra_states={self.state.ORDER: [CallbackQueryHandler(self.process_order)]}
        )
        self.order_module = self.OrderingModule(self)
        self.db_info = bx_utils.db.get_committee_info(self.name)
        drinks = ["Shots", "Rainbow Road", "Collective Suicide", "Beer", "Mojito", "Sex on the beach", "Cuba semi libre", "Easy Peasy", "Summer Special", "Manzanade"]
        table_numbers = list(range(18))
        self.tables_keyboard = self.create_keyboard(table_numbers)
        self.drink_keyboard = self.create_keyboard(drinks)
        self.user_id = ''
    async def menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        
        await self.send_message(update, context, text="This is the current menu")
        file_path = utils.config.ROOT + '/data/menu.jpg'
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

    async def drink(self, update: Update, context: CallbackContext):
        query = update.callback_query
        await query.answer()
        data = query.data
        if query.data == 'Nay':
            await query.edit_message_text('Alright')
            return self.state.HOME

    async def order(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        self.order_module.build()
        self.user_id = update.effective_user.id
        await self.send_message(update, context, "What do you want to order?", reply_markup=self.order_module.keyboard)
        return self.state.ORDER

    async def process_order(self, update:Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        cont, stage, order = self.order_module.process(query.data)
        self.order_module.build()
        if not cont:
            if stage == 'Confirmed':
                index = await self.send_order(order, context, update.effective_user)
                await query.edit_message_text(f'Your order (#{index}) is being currently processed, you will be messaged once the order is ready')
            elif stage == 'Not ordered':
                await query.edit_message_text('Your order has been cancelled')
            return self.state.HOME
        if stage == 'quantity':
            await query.edit_message_text(f'How many {self.order_module.drink} do you want?', reply_markup=self.order_module.keyboard)
            return self.state.ORDER
        if stage == 'more':
            await query.edit_message_text('Do you want to order any other drinks?\nYou already have:\n'+ '\n'.join([f'• {drinks[1]} of {drinks[0]}' for drinks in order]), reply_markup=self.order_module.keyboard)
            return self.state.ORDER
        if stage == 'snacks':
            await query.edit_message_text('Do you want to add some snacks to your order just for 0.5€', reply_markup=self.order_module.keyboard)
            return self.state.ORDER
        if stage == 'confirmation':
            order_message = f'Do you confirm your order? \n' + '\n'.join([f'• {drinks[1]} of {drinks[0]}' for drinks in order])
            await query.edit_message_text(order_message, reply_markup=self.order_module.keyboard)
            return self.state.ORDER
        if stage == 'drink':
            await query.edit_message_text("What do you want to order?", reply_markup=self.order_module.keyboard)
            return self.state.ORDER


    async def send_order(self, order, context, user):
        try:
            index = int(list(bx_utils.db.get_committee_info(".9 Bar orders").keys())[-1]) + 1
        except IndexError:
            index = 1
        message = f'Order number {index} from {user.full_name}: \n' + '\n'.join([f'• {drinks[1]} of {drinks[0]}' for drinks in order])
        await context.bot.send_message(BAR_ID, text=message)
        bx_utils.db.extra_committee_info(".9 Bar orders", index, self.user_id)
        return index

    class OrderingModule:
        class State(enum.Enum):
            DRINK = 1
            QUANTITY = 2
            MORE = 3
            TABLE = 4
            CONFIRMATION = 5
            SNACKS = 6

        def __init__(self, bar):
            self.order = []  # List of tuples (drink, quantity)
            self.drink = ''
            self.params = {}
            self.state = self.State.DRINK
            self.bar = bar
            self.keyboard = None

        def build(self):
            if self.state == self.State.DRINK:
                self._build_drink()
            elif self.state == self.State.QUANTITY:
                self._build_quantity()
            elif self.state == self.State.MORE:
                self._build_more()
            elif self.state == self.State.TABLE:
                self._build_table()
            elif self.state == self.State.SNACKS:
                self._build_snakcs()
            elif self.state == self.State.CONFIRMATION:
                self._build_confirmation()

        def _build_drink(self):
            drinks = bx_utils.db.get_committee_info(".9 Bar")["drinks"]
            list_drinks = bx_utils.db.db_to_list(drinks)
            self.keyboard = self.bar.create_keyboard(list_drinks)

        def _build_quantity(self):
            options = list(range(1,5))
            self.keyboard = self.bar.create_keyboard(options)

        def _build_more(self):
            self.keyboard = self.bar.create_keyboard(["Yay"])

        def _build_snacks(self):
            snacks = bx_utils.db.get_committee_info(".9 Bar")["snacks"]
            list_snacks = bx_utils.db.db_to_list(snacks)
            self.keyboard = self.bar.create_keyboard(list_snacks)
        def _build_table(self):
            self.keyboard = self.bar.create_keyboard(list(range(20)))
        def _build_confirmation(self):
            self.keyboard = self.bar.create_keyboard(["Yay"])

        def process(self, call_data):
            #Gets the callback data and returns a tuple (continue, state, final_result)
            if self.state == self.State.DRINK:
                if call_data == 'Nay':
                    if self.order == []:
                        return False, 'Not ordered', None
                    self.state = self.State.MORE
                    return True, 'more', self.order
                if call_data == 'Yay':
                    return True, 'drink', None
                self.drink = call_data
                self.state = self.State.QUANTITY
                return True, 'quantity', call_data
            elif self.state == self.State.QUANTITY:
                if call_data != 'Nay':
                    self.order.append((self.drink, call_data))
                self.state = self.State.MORE
                return True, 'more', self.order
            elif self.state == self.State.MORE:
                if call_data == 'Yay':
                    self.state = self.State.DRINK
                    return True, 'drink', None
                else:
                    self.state = self.State.CONFIRMATION
                    return True, 'snacks', self.order
            elif self.state == self.State.SNACKS:
                if call_data != 'Nay':
                    self.order.append((call_data, 1))
                return True, 'confirmation', self.order
            elif self.state == self.State.CONFIRMATION:
                self.state = self.State.DRINK
                order = self.order
                self.order = []
                if call_data == 'Yay':
                    return False, 'Confirmed', order
                return False, 'Not ordered', None





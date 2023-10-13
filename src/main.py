import re
import time
import math
import random
import string
import Lore
import Committees
import utils
import bx_utils

from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("SAILORE_BX_BOT")
gc_id = int(os.getenv("GC_ID"))
ids = os.getenv("IDS")
import json

with open(utils.config.ROOT + '/data/Initial.json', encoding='utf-8') as f:
    texts = json.load(f)

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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

logger = bx_utils.logger(__name__)

INITIAL, LORE, CONTINUE, COMMITTEES, REQUEST, MASTER, MASTER_PASS, ORDER = range(8)


def message_wait(message):
    return math.log(len(message), 10) - 1


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for input."""
    if update.effective_chat.id == -4050559023:
        return INITIAL #To avoid problems in gcs only made for certain functionalities
    for message in texts["start"]:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(message_wait(message))
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    bx_utils.db.add_to_db(update.effective_user)
    return INITIAL


async def generic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Response depending on the message received"""
    if update.effective_chat.id == -4050559023:
        return INITIAL #To avoid problems in gcs only made for certain functionalities
    message = update.message.text
    message = message.strip('/')
    keys = texts.keys()
    for key in keys:
        if re.match(key, message.lower()):
            text = texts[key]
            break
    else:
        text = texts["predetermined"]
    for message in text:
        bx_utils.db.add_to_db(update.effective_user)
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        time.sleep(message_wait(message))
        await context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    return INITIAL


async def request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allow users to input requests"""
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="What do you want to tell the tech support")
    return REQUEST

async def orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Allows bartenders to mark orders as ready"""
    if update.effective_chat.id != -4050559023:
        return generic(update, context)
    orders = bx_utils.db.get_committee_info(".9 Bar orders")
    if orders == {}:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="There is no orders at the moment")
    keyboard = create_keyboard(list(orders.keys()))
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Which order do you want to mark as ready?",
                                   reply_markup=keyboard)
    return ORDER

async def process_order(update: Update, context: CallbackContext):
    orders = bx_utils.db.get_committee_info(".9 Bar orders")
    query = update.callback_query
    await query.answer()
    if query.data == 'Nay':
        await query.edit_message_text(text='Alright')
        return INITIAL
    chat_id = orders[query.data]
    await context.bot.send_message(chat_id=chat_id,
                             text="Your order is ready, come to the bar to pick it up")
    await query.edit_message_text(text="User has been notified")
    bx_utils.db.delete_committee_info(".9 Bar orders", query.data)
    return INITIAL
async def manage_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request_made = update.message.text
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="The support has been informed and it will be taken into consideration")
    await context.bot.send_message(chat_id=gc_id,
                                   text=f'Request from {update.effective_user.name}: \n{request_made}')
    return INITIAL


def get_committees_with_json():
    with open('./data/Committees/committees.json') as file:
        committees = json.load(file)
    json_file = list(committees.keys())
    json_file.sort()
    return json_file


def get_committees_with_program():
    program = Committees.names
    program.sort()
    return program


async def master(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Master access for management of important things"""
    id = str(update.effective_chat.id)
    if not id in ids:
        return generic(update, context)
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Succesfully entered the master admin lord of the bots mode")
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="From here you can check the committees /status or get a new /password for a given committee")

    return MASTER


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    program = bx_utils.db.list_to_telegram(get_committees_with_program())
    json_file = bx_utils.db.list_to_telegram(get_committees_with_json())
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"These committees have a program: \n{program}")
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"These committees have a json file: \n{json_file}")
    return MASTER


async def password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    committees_without_access = []
    for name in get_committees_with_program():
        access = bx_utils.db.get_committee_access(name)
        if access == {}:
            committees_without_access.append(name)
    reply_markup = create_keyboard(committees_without_access)
    if reply_markup is None:
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text=f"All accessible committees have access established")
        return INITIAL
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"These committeees don't have access: {committees_without_access}",
                                   reply_markup=reply_markup)
    return MASTER_PASS


async def receive_pass(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    if query.data == 'Nay':
        await query.edit_message_text(text="Alright")
        return INITIAL
    committee_name = query.data
    new_password = committee_name + ':' + ''.join(random.choices(string.digits + string.ascii_letters, k=10))
    bx_utils.db.add_one_time_pass(new_password, committee_name)
    await query.edit_message_text(text=new_password)
    return INITIAL


def create_balanced_layout(names):
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


def create_keyboard(names):
    layout = create_balanced_layout(names)
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


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(BOT_TOKEN).concurrent_updates(True).build()
    members = Lore.Members()
    conv_handler = ConversationHandler(
        #block=False,
        entry_points=[CommandHandler("start", start), MessageHandler(filters.TEXT, start)],
        states={
            INITIAL: [
                CommandHandler("master", master),
                CommandHandler("ready", orders),
                # Initial state of the bot in which it can be asked about gems, the lore and committees
                Lore.GemHandler.handler,
                MessageHandler(
                    filters.Regex(re.compile(r"l'?ore", re.IGNORECASE)), members.intro
                ),
                MessageHandler(
                    filters.Regex(re.compile(r"com+it+e+s?", re.IGNORECASE)), Committees.intro
                    # added the question marks cuz people tend to mispell this word
                ),
                CommandHandler("request", request)
            ] + Committees.committees,
            LORE: [
                # State of the bot in which it can be asked about the different sailore members
                CallbackQueryHandler(members.member)
            ],
            CONTINUE: [
                # State of the bot in which it is asked if it wants to continue asking about sailore members
                CallbackQueryHandler(members.more)
            ],
            REQUEST: [
                MessageHandler(filters.TEXT, manage_request)
            ],
            MASTER: [
                CommandHandler("status", status),
                CommandHandler("password", password)
            ],
            MASTER_PASS: [
                CallbackQueryHandler(receive_pass)
            ],
            ORDER : [
                CallbackQueryHandler(process_order)
            ]
        },
        fallbacks=[MessageHandler(filters.TEXT, generic)],
        per_chat=False
    )

    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
import json
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .cacher import save_user_current_state, get_user_current_state
from .config import chat_bot_nodes
from .constants import NodeTypes, NodeNames
from .fake_message_texts import fake_message_texts

logger = logging.getLogger(__name__)


def find_node(name):
    return chat_bot_nodes[name]


def get_text(name):
    # TODO: Добавить тра кетч
    return fake_message_texts[name]


def start(bot, update):
    tg_user_id = update.message.from_user.id
    # try:
    #     existing_profile = Profile.objects.filter(telegram_id=tg_user_id).first()
    # except (OperationalError, InterfaceError):
    #     db_close()
    #     existing_profile = Profile.objects.filter(telegram_id=tg_user_id).first()

    save_user_current_state(tg_user_id, NodeNames.START)
    process_node(bot, update.message.chat_id, update.message.from_user.id)


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"' % (update, error))


def choose_menu_item(bot, update):
    tg_user_id = update.callback_query.from_user.id
    user_current_state_id = get_user_current_state(tg_user_id)
    callback_data = json.loads(update.callback_query.data)

    if user_current_state_id == callback_data["from_node"]:
        save_user_current_state(tg_user_id, callback_data["next_node"])
        process_node(bot, update.callback_query.message.chat.id, update.callback_query.from_user.id)


def process_node(bot, chat_id, tg_user_id):
    user_state_id = get_user_current_state(tg_user_id)
    user_state = find_node(user_state_id)

    if user_state.get('type') == NodeTypes.MESSAGE:
        show_message(bot, chat_id, user_state.get('message'))
        save_user_current_state(tg_user_id, user_state.get('nextState'))
        process_node(bot, chat_id, tg_user_id)

    if user_state.get('type') == NodeTypes.MENU:
        show_menu(bot, chat_id, user_state_id, user_state)


def show_menu(bot, chat_id, user_state_id, user_state):
    items = user_state['items']
    keyboard = []

    for item in items:
        keyboard.append([InlineKeyboardButton(text=get_text(item['text']), callback_data=json.dumps(
            {'from_node': user_state_id, 'next_node': item['nextState']}))])
    reply_markup = InlineKeyboardMarkup(keyboard)

    bot.send_message(chat_id, text=get_text(user_state['message']), reply_markup=reply_markup)


def show_message(bot, chat_id, message):
    bot.send_message(chat_id, text=get_text(message))

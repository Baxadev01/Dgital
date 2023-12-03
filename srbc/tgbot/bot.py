# -*- coding: utf-8 -*-

import logging

from django.db import ProgrammingError
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import CallbackContext

from content.utils import store_dialogue_reply
from srbc.tgbot.cache import get_user_current_data, save_user_current_data, remove_user_current_data
from srbc.tgbot.config import NodeNames
from srbc.tgbot.models import TGBotNode
from srbc.tgbot.utils import check_user

logger = logging.getLogger(__name__)


class TGBotManager(object):
    nodes = {}
    debug_info = []

    def register(self, key):
        def decorator(node):
            if not issubclass(node, TGBotNode):
                logger.error("Import WTF %s" % key)
                return node

            logger.info("Import OK %s" % key)

            if key in self.nodes:
                logger.error('Duplicate key found during nodes registration', extra={'key': key})
                return node

            node.node_key = key
            self.nodes[key] = node

            return node

        return decorator

    def get_node(self, key):
        """

        :param key:
        :returns: Class


        """
        node_class = self.nodes.get(key)
        if not node_class:
            raise ProgrammingError("Node with the key '%s' is not registered" % key)

        return node_class

    def process(self, tgupdate: Update, context: CallbackContext):
        # Get user from Update
        tg_user_id = tgupdate.message.from_user.id

        try:
            self._process(context.bot, tgupdate, tg_user_id)
        except Exception as exc:
            logger.exception(exc)
            text = "Извините, я что-то задумался..." \
                   "Повторите своё последнее сообщение еще раз, пожалуйста?.."
            context.bot.send_message(chat_id=tg_user_id, text=text)

    def _process(self, tgbot, tgupdate, tg_user_id):
        # get user and check it
        existing_user, error_message = check_user(tg_user_id=tg_user_id)
        if error_message:
            msg = tgbot.send_message(
                chat_id=tg_user_id,
                text=error_message,
                reply_markup=ReplyKeyboardRemove(),
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            if existing_user:
                store_dialogue_reply(
                    user=existing_user, message=error_message, message_id=msg.message_id,
                    tg_user_id=tg_user_id
                )
            remove_user_current_data(user_id=tg_user_id)
            return

        # Get Current State
        prev_node_data = get_user_current_data(user_id=tg_user_id)
        node_key = prev_node_data.get('node_key') or NodeNames.MAIN_MENU

        last_node_data = self._process_node(
            node_key=node_key, tgbot=tgbot, tgupdate=tgupdate, tg_user_id=tg_user_id,
            existing_user=existing_user, prev_node_data=prev_node_data
        )
        if last_node_data != prev_node_data:
            save_user_current_data(user_id=tg_user_id, **last_node_data)

    def _process_node(self, node_key, tgbot, tgupdate, tg_user_id, existing_user, prev_node_data):
        node_class = self.get_node(node_key)
        node = node_class(
            bot=tgbot, update=tgupdate, user=existing_user, tg_user_id=tg_user_id, prev_node_data=prev_node_data
        )
        next_node_key = node.process_request()

        if next_node_key:
            auto_node_class = self.get_node(next_node_key)
            if auto_node_class.auto_processing:
                last_node_data = self._process_node(
                    node_key=next_node_key, tgbot=tgbot, tgupdate=tgupdate, tg_user_id=tg_user_id,
                    existing_user=existing_user, prev_node_data=prev_node_data
                )
            else:
                last_node_data = {
                    'node_key': next_node_key,
                    'keyboard_data': node.get_keyboard(),
                    'partial_messages': node.partial_messages
                }
        else:
            last_node_data = prev_node_data

        return last_node_data


bot_manager = TGBotManager()

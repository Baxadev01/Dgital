# -*- coding: utf-8 -*-
import logging
from django.conf import settings

from django.contrib.auth.models import User
from django_telegrambot.apps import DjangoTelegramBot
from telegram import Update
from telegram.ext import BaseFilter, CommandHandler, Filters, MessageHandler, Updater

from srbc.chatbot.bot import (check_participant_joined, check_participant_left, db_close, debug, dialogue, error,
                              get_userinfo_by_fwd, no_img_pls, question_add, question_reply_general,
                              send_participant_contact, start, whereami)
from srbc.tgbot.bot import bot_manager
from srbc.tgbot.commands import reload_bot_texts, start, send_login_link
from srbc.tgbot.utils import parse_contact

logger = logging.getLogger(__name__)


class _StaffFilter(BaseFilter):
    def filter(self, message):
        tg_user_id = message.from_user.id
        srbc_user = User.objects.filter(profile__telegram_id=tg_user_id).first()
        if not srbc_user:
            return False

        return srbc_user.is_staff

    
    def __call__(self, update: Update):
        return self.filter(update.message)


StaffFilter = _StaffFilter()


def main():
    logger.info("Loading handlers for telegram bot")

    # Default dispatcher (this is related to the first bot in settings.DJANGO_TELEGRAMBOT['BOTS'])
    dp = DjangoTelegramBot.dispatcher

    dp.add_handler(CommandHandler("start", start))

    dp.add_handler(CommandHandler("whereami", whereami))

    dp.add_handler(CommandHandler("reconnect", db_close))
    dp.add_handler(
        CommandHandler(
            "contact",
            send_participant_contact,
            pass_args=True,
            filters=StaffFilter & Filters.chat_type.private
        )
    )

    dp.add_handler(CommandHandler("reload", reload_bot_texts))

    dp.add_handler(CommandHandler("login", send_login_link))

    # dp.add_handler(
    #     CommandHandler(
    #         "info",
    #         get_userinfo_by_id,
    #         pass_args=True,
    #         filters=StaffFilter & Filters.private
    #     )
    # )

    dp.add_handler(MessageHandler((Filters.all | Filters.command) & ~Filters.update.edited_message, debug), 0)

    dp.add_handler(
        MessageHandler(Filters.chat_type.private & (Filters.all | Filters.command) & ~Filters.update.edited_message, dialogue), 10
    )

    dp.add_handler(
        MessageHandler(Filters.chat_type.private & Filters.forwarded & StaffFilter & ~Filters.update.edited_message, 
            get_userinfo_by_fwd), 20
    )

    dp.add_handler(
        MessageHandler(Filters.chat_type.private & Filters.text & ~Filters.command & ~Filters.update.edited_message, bot_manager.process), 20
    )

    dp.add_handler(MessageHandler(Filters.chat_type.private & Filters.photo & ~Filters.update.edited_message, no_img_pls), 20)
    dp.add_handler(MessageHandler(Filters.chat_type.private & Filters.contact, parse_contact), 20)

    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, check_participant_joined), 30)
    dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, check_participant_left), 30)

    dp.add_handler(MessageHandler(Filters.chat_type.groups, question_add), 40)
    dp.add_handler(MessageHandler(Filters.chat_type.groups & Filters.reply, question_reply_general), 50)

    # dp.add_handler(MessageHandler(Filters.private, maintenance), 3)

    # log all errors
    dp.add_error_handler(error)

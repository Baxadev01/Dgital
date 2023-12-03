import logging
import typing as ty

from django.db import connection, OperationalError, InterfaceError
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update, InlineKeyboardMarkup, InlineKeyboardButton, LoginUrl
from telegram.ext import CallbackContext

from content.utils import store_dialogue_reply
from srbc.models import Profile
from srbc.tgbot.commands.cmd_start import _get_profile, start
from srbc.tgbot.config import NodeTranslations
from srbc.tgbot.utils import translate

__all__ = ('send_login_link', )

from srbc.utils.auth import get_short_time_jwt

logger = logging.getLogger(__name__)


def send_login_link(update: Update, context: CallbackContext) -> None:
    tg_user_id = update.message.from_user.id

    try:
        profile = _get_profile(tg_user_id=tg_user_id)
    except (OperationalError, InterfaceError):
        connection.close()
        profile = _get_profile(tg_user_id=tg_user_id)

    if not profile:
        return start(update, context)

    url_template = LoginUrl('https://lk.selfreboot.camp/accounts/login/tg/')

    login_button = InlineKeyboardButton(text='Личный кабинет', login_url=url_template)

    custom_keyboard = [[login_button]]

    login_message = "Для перехода в личный кабинет нажмите кнопку под этим сообщением."

    msg = context.bot.send_message(
        chat_id=tg_user_id,
        text=login_message,
        reply_markup=InlineKeyboardMarkup(custom_keyboard)
    )
    store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

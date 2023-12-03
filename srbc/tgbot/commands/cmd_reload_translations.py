import logging
import typing as ty

from django.db import connection, OperationalError, InterfaceError
from telegram.bot import Bot
from telegram import Update
from telegram.ext import CallbackContext

from content.utils import store_dialogue_reply
from srbc.models import User
from srbc.tgbot.utils import rebuild_translations

__all__ = ('reload_bot_texts', )

logger = logging.getLogger(__name__)


def _get_staff_user(tg_user_id: int) -> ty.Optional[User]:
    return User.objects.filter(profile__telegram_id=tg_user_id, is_staff=True).first()


def reload_bot_texts(update: Update, context: CallbackContext) -> None:
    tg_user_id = update.message.from_user.id

    try:
        staff_user = _get_staff_user(tg_user_id=tg_user_id)
    except (OperationalError, InterfaceError):
        connection.close()
        staff_user = _get_staff_user(tg_user_id=tg_user_id)

    if staff_user:
        rebuild_translations()
        message = 'Текстовые метки обновлены'
    else:
        message = 'Access denied'

    msg = context.bot.send_message(chat_id=tg_user_id, text=message)
    store_dialogue_reply(user=staff_user, message=message, message_id=msg.message_id, tg_user_id=tg_user_id)

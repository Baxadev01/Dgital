import logging
import typing as ty

from django.db import connection, OperationalError, InterfaceError
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext

from content.utils import store_dialogue_reply
from srbc.models import Profile
from srbc.tgbot.config import NodeTranslations
from srbc.tgbot.utils import translate

__all__ = ('start', '_get_profile', )

logger = logging.getLogger(__name__)


def _get_profile(tg_user_id: int) -> ty.Optional[Profile]:
    return Profile.objects.filter(telegram_id=tg_user_id).first()


def start(update: Update, context: CallbackContext) -> None:
    tg_user_id = update.message.from_user.id

    try:
        profile = _get_profile(tg_user_id=tg_user_id)
    except (OperationalError, InterfaceError):
        connection.close()
        profile = _get_profile(tg_user_id=tg_user_id)

    if profile:
        if profile.is_active:
            text = translate(NodeTranslations.CMD__START__TXT__ALREADY_ACTIVE)
            parse_mode = None
        else:
            text = translate(NodeTranslations.CMD__START__TXT__ALREADY_BLOCKED)
            parse_mode = 'Markdown'

        msg = context.bot.send_message(chat_id=tg_user_id, text=text, parse_mode=parse_mode)
        store_dialogue_reply(user=profile.user, message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
    else:
        contact_keyboard = KeyboardButton(
            text=translate(NodeTranslations.CMD__START__TXT__SEND_CONTACT_BTN), request_contact=True
        )
        custom_keyboard = [[contact_keyboard]]
        msg = context.bot.send_message(
            chat_id=tg_user_id,
            text=translate(NodeTranslations.CMD__START__TXT__REGISTRATION_PHONE_IS_REQUIRED),
            reply_markup=ReplyKeyboardMarkup(custom_keyboard)
        )
        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

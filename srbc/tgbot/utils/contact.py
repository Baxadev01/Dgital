import re
import typing as ty

from django.contrib.auth.models import UserManager, User
from django.db import connection, OperationalError, InterfaceError
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import CallbackContext

from content.utils import store_dialogue_reply
from srbc.models import Profile
from srbc.tgbot.commands import send_login_link
from srbc.tgbot.config import NodeTranslations
from srbc.tgbot.utils import translate

__all__ = ('parse_contact',)


def _get_profile(tg_user_id: int) -> ty.Optional[Profile]:
    return Profile.objects.filter(telegram_id=tg_user_id).first()


def parse_contact(update: Update, context: CallbackContext) -> None:
    tg_user_id = update.message.from_user.id
    contact = update.message.contact

    phone_number = contact.phone_number

    non_decimal = re.compile(r'[^\d]+')
    phone_number = non_decimal.sub('', phone_number)
    phone_number = phone_number.lstrip('0')

    user_profile = None

    if len(phone_number) == 10 and phone_number[0] == '9':
        phone_number = '7%s' % phone_number

    if len(phone_number) == 11 and phone_number[0] == '8':
        phone_number = '7%s' % phone_number[1:]

    if contact.user_id != tg_user_id:
        msg = context.bot.send_message(
            chat_id=update.message.chat_id,
            text=translate(NodeTranslations.CONTACT__TXT__CONFIRMATION_WRONG_USER),
            reply_markup=ReplyKeyboardRemove()
        )
        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
        return

    try:
        profile = _get_profile(tg_user_id=tg_user_id)
    except (OperationalError, InterfaceError):
        connection.close()
        profile = _get_profile(tg_user_id=tg_user_id)

    if profile:
        if profile.is_active:
            msg = context.bot.send_message(
                chat_id=update.message.chat_id,
                text=NodeTranslations.CONTACT__TXT__ALREADY_ACTIVE,
                reply_markup=ReplyKeyboardRemove()
            )
            store_dialogue_reply(user=profile.user, message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
            return

    else:
        base_username = update.message.from_user.username

        if not base_username:
            base_username = 'tg%s' % update.message.from_user.id

        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = '%s.%s' % (base_username, counter,)
            counter += 1

        user = UserManager.create_user(
            username=username
        )

        user_profile = Profile(user=user, mobile_number=phone_number)
        user_profile.save(force_insert=True)

    if not user_profile:
        try:
            user_profile = Profile.objects.get(mobile_number=phone_number)
        except Profile.DoesNotExist:
            msg = context.bot.send_message(
                chat_id=update.message.chat_id,
                text=translate(NodeTranslations.CONTACT__TXT__CONFIRMATION_UNKNOWN_PHONE_NUMBER)
            )
            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
            return

    user_profile.telegram_id = tg_user_id
    user_profile.telegram_first_name = update.message.from_user.first_name
    user_profile.telegram_last_name = update.message.from_user.last_name
    user_profile.save(update_fields=['telegram_id', 'telegram_last_name', 'telegram_first_name'])

    if user_profile.is_active and user_profile.communication_mode == 'CHANNEL':
        msg_text = translate(NodeTranslations.CONTACT__TXT__SUCCESS__CHANNEL)
        msg_text = msg_text.format(USER_ID=user_profile.user_id)
    else:
        msg_text = translate(NodeTranslations.CONTACT__TXT__SUCCESS)
        msg_text = msg_text.format(USER_ID=user_profile.user_id)

    msg = context.bot.send_message(
        chat_id=update.message.chat_id,
        text=msg_text,
        reply_markup=ReplyKeyboardRemove()
    )

    store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

    return send_login_link(update, context)

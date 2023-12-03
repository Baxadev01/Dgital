# -*- coding: utf-8 -*-
import logging
import re

import emoji
import pytz
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection, OperationalError, InterfaceError
from django.utils import timezone
from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import BaseFilter, CallbackContext
from telegram.utils.helpers import escape_markdown

from content.models import TGChatParticipant, Dialogue, ChatQuestion, TGChat
from content.utils import store_dialogue_reply
from srbc.chatbot.actions import CHATBOT_ACTIONS, ChatbotMessageAction
from srbc.chatbot.config import chatbot_tags_to_process
from srbc.chatbot.filters import (
    ChatbotMessageFilter
)
from srbc.chatbot.messages import bot_messages, bot_ui
from srbc.chatbot.messages import (
    response_hashtags_multiple, response_hashtags_not_found,
    response_not_accepted,
)
from srbc.models import Profile, UserNote, GTTResult, Checkpoint, CheckpointPhotos, TariffGroup

logger = logging.getLogger(__name__)

chatbot_system_tags = list(chatbot_tags_to_process.keys())


def db_close(update: Update, context: CallbackContext) -> None:
    connection.close()


def maintenance(bot, update):
    msg = bot.send_message(
        chat_id=update.message.chat_id,
        text=bot_messages.under_maintainance
    )
    # logger.info(msg)
    # store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
    return


def send_participant_contact(update: Update, context: CallbackContext) -> None:
    if not context.args:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=bot_messages.contact_arg_required,
            reply_to_message_id=update.message.message_id
        )
        return

    lookup_ig = context.args[0]  # upper() ?

    participant_profile = Profile.objects.filter(user__username=lookup_ig).first()

    if not participant_profile:
        participant_profile = Profile.objects.filter(instagram=lookup_ig).first()

    if not participant_profile:
        participant_profile = Profile.objects.filter(user_id=lookup_ig).first()

    if not participant_profile:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=bot_messages.contact_not_found,
            reply_to_message_id=update.message.message_id
        )
        return

    if not participant_profile.telegram_id:
        context.bot.send_message(
            chat_id=update.message.chat_id,
            text=bot_messages.contact_not_known,
            reply_to_message_id=update.message.message_id
        )
        return

    participant_name = ''

    if participant_profile.user.first_name:
        participant_name += participant_profile.user.first_name + ' '

    participant_name += participant_profile.user.username

    context.bot.send_contact(
        chat_id=update.message.chat_id,
        reply_to_message_id=update.message.message_id,
        first_name=participant_name,
        last_name=participant_profile.user.last_name,
        phone_number='+%s' % participant_profile.mobile_number
    )


def start(bot, update):
    tg_user_id = update.message.from_user.id
    try:
        existing_profile = Profile.objects.filter(telegram_id=tg_user_id).first()
    except (OperationalError, InterfaceError):
        db_close()
        existing_profile = Profile.objects.filter(telegram_id=tg_user_id).first()

    if existing_profile:
        if existing_profile.is_active:
            msg = bot.send_message(
                chat_id=update.message.chat_id,
                text=bot_messages.already_registered_and_active
            )
            # logger.info(msg)
            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

            return
        else:
            msg = bot.send_message(
                chat_id=update.message.chat_id,
                text=bot_messages.already_registered_but_blocked,
                parse_mode='Markdown'
            )
            # logger.info(msg)
            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
            return

    contact_keyboard = KeyboardButton(text=bot_ui.send_contact_btn, request_contact=True)
    custom_keyboard = [[contact_keyboard]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard)

    msg = bot.send_message(
        chat_id=update.message.chat_id,
        text=bot_messages.registration_phone_is_required,
        reply_markup=reply_markup,
    )
    store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
    # logger.info(msg)


def whereami(update: Update, context: CallbackContext) -> None:
    tg_user_id = update.message.from_user.id

    try:
        existing_profile = Profile.objects.filter(telegram_id=tg_user_id).first()
    except (OperationalError, InterfaceError):
        db_close()
        existing_profile = Profile.objects.filter(telegram_id=tg_user_id).first()

    if not existing_profile:
        return

    if not existing_profile.user.is_superuser:
        return

    msg_text = "ID чата: *%s*" % update.message.chat_id

    msg = context.bot.send_message(
        chat_id=update.message.chat_id,
        text=msg_text,
        parse_mode='Markdown',
        reply_to_message_id=update.message.message_id,
        disable_web_page_preview=True,
    )
    # logger.info(msg)


def parse_contact(bot, update):
    tg_user_id = update.message.from_user.id
    contact = update.message.contact
    try:
        existing_profile = Profile.objects.filter(telegram_id=tg_user_id).first()
    except (OperationalError, InterfaceError):
        db_close()
        existing_profile = Profile.objects.filter(telegram_id=tg_user_id).first()

    if existing_profile:
        if existing_profile.is_active:
            msg = bot.send_message(
                chat_id=update.message.chat_id,
                text=bot_messages.already_registered_and_active
            )
            # logger.info(msg)
            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

            return

    if contact.user_id != update.message.chat_id:
        msg = bot.send_message(
            chat_id=update.message.chat_id,
            text=bot_messages.contact_confirmation_wrong_user
        )
        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
        # logger.info(msg)
        return

    phone_number = contact.phone_number

    non_decimal = re.compile(r'[^\d]+')
    phone_number = non_decimal.sub('', phone_number)

    phone_number = phone_number.lstrip('0')

    if len(phone_number) == 10 and phone_number[0] == '9':
        phone_number = '7%s' % phone_number

    if len(phone_number) == 11 and phone_number[0] == '8':
        phone_number = '7%s' % phone_number[1:]

    try:
        user_profile = Profile.objects.get(mobile_number=phone_number)
    except ObjectDoesNotExist:
        msg = bot.send_message(
            chat_id=update.message.chat_id,
            text=bot_messages.contact_confirmation_unknown_phone_number
        )
        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
        # logger.info(msg)

        return

    user_profile.telegram_id = tg_user_id
    user_profile.telegram_first_name = update.message.from_user.first_name
    user_profile.telegram_last_name = update.message.from_user.last_name
    user_profile.save(
        update_fields=['telegram_id', 'telegram_last_name', 'telegram_first_name'])

    msg_text = "Я вас запомнил, записал и, на всякий случай, сделал эскиз карандашом. "
    if user_profile.is_active and user_profile.communication_mode == TariffGroup.COMMUNICATION_MODE_CHANNEL:
        msg_text += "Теперь я буду слушать ваши сообщения с рабочими хэштегами " \
                    "и передавать их в штаб для обработки"

    msg = bot.send_message(
        chat_id=update.message.chat_id,
        text=msg_text,
        reply_markup=ReplyKeyboardRemove()
    )
    store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
    # logger.info(msg)

    # if user_profile.wave_id and user_profile.wave.tg_channel_slug:
    #     channel_link = "https://t.me/joinchat/%s" % user_profile.wave.tg_channel_slug
    #
    #     msg = bot.send_message(
    #         chat_id=update.message.chat_id,
    #         text=u"Вот ссылка для присоединения к информационному каналу: %s" % channel_link
    #     )
    #     logger.info(msg)


def message_received(bot, update):
    # logger.info(update)
    question_ask(bot=bot, update=update)


def no_img_pls(update: Update, context: CallbackContext) -> None:
    chat_message = update.message or update.edited_message
    if chat_message is None:
        return

    author_tg_id = chat_message.from_user.id
    try:
        User.objects.get(profile__telegram_id=author_tg_id)
    except ObjectDoesNotExist:
        response_not_accepted(context.bot, update)
        msg = context.bot.send_message(
            chat_id=update.message.chat_id,
            text="Кажется, мы не знакомы. Пожалуйста, представься при помощи команды /start"
        )
        # logger.info(msg)
        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
        return

    response_not_accepted(context.bot, update)
    msg = context.bot.send_message(
        chat_id=update.message.chat_id,
        text="Вместо того, чтобы послать картинку - пожалуйста, опиши словами, что на ней. И не забудь про хэштеги."
    )
    store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
    # logger.info(msg)


def question_ask(bot, update):
    chat_message = update.message

    if chat_message is None:
        return

    author_tg_id = chat_message.from_user.id

    try:
        current_user = User.objects.get(profile__telegram_id=author_tg_id)
    except ObjectDoesNotExist:
        response_not_accepted(bot, update)
        msg = bot.send_message(
            chat_id=update.message.chat_id,
            text="Кажется, мы не знакомы. Пожалуйста, представься при помощи команды /start"
        )
        # logger.info(msg)
        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
        return msg
    except (OperationalError, InterfaceError):
        db_close()
        msg = bot.send_message(
            chat_id=update.message.chat_id,
            text=bot_messages.temporary_error
        )
        # logger.info(msg)
        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
        return

    if not current_user.profile.is_active:
        if current_user.profile.wave_id:
            response_not_accepted(bot, update)
            msg = bot.send_message(
                chat_id=update.message.chat_id,
                text="Ваш аккаунт был заблокирован.\n"
                     "По всем вопросам обращайтесь в личные сообщения страницы "
                     "[selfrebootcamp в Facebook](https://www.facebook.com/messages/t/selfrebootcamp)",
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
            # logger.info(msg)
            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

        else:
            response_not_accepted(bot, update)
            msg = bot.send_message(
                chat_id=update.message.chat_id,
                text="Я сохраняю сообщения только от участников проекта. "
                     "Вы не в списке участников. "
                     "Если считаете, что произошла ошибка – пожалуйста, свяжитесь с командой в "
                     "[личных сообщениях страницы](https://facebook.com/selfrebootcamp/)",
                parse_mode='Markdown'
            )
            # logger.info(msg)
            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
        return

    emojies = ''.join(c for c in chat_message.text if c in emoji.UNICODE_EMOJI)
    if len(emojies):
        response_not_accepted(bot, update)
        msg = bot.send_message(
            chat_id=update.message.chat_id,
            text="Сообщение содержит emoji.\n"
                 "Пожалуйста, перепишите сообщение в соответствии с правилами задавания вопросов SELFREBOOTCAMP",
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
        return

    entities = chat_message.entities

    message_tags = [chat_message.text[e.offset:e.offset + e.length].lower() for e in entities if e.type == 'hashtag']
    message_system_tags = [t for t in message_tags if t in chatbot_system_tags]

    if len(message_tags) > 1:
        return response_hashtags_multiple(bot, update)
    elif not len(message_system_tags):
        return response_hashtags_not_found(bot, update)

    work_tag = message_system_tags[0]
    system_tag = chatbot_tags_to_process.get(work_tag)
    checks = system_tag.get('checks')
    checks_passed = True

    if checks:
        for _check in checks:
            check_class = _check.get('class')
            check_args = _check.get('params', dict())
            if issubclass(check_class, ChatbotMessageFilter):
                check_entity = check_class(bot, update, current_user, system_tag, **check_args)
                if not check_entity.get_result():
                    checks_passed = False
                    break
            else:
                raise Exception("Programming error: check %s is not ChatbotMessageFilter" % check_class.__class__)

    if not checks_passed:
        return

    actions = system_tag.get('actions', [])
    for _action in actions:
        action_class = CHATBOT_ACTIONS.get(_action.get('action'))
        params = _action.get('params', dict())
        if not action_class:
            continue
        if not issubclass(action_class, ChatbotMessageAction):
            continue

        x = action_class(bot, update, current_user, system_tag, **params)


def check_channel_permissions(bot, update):
    pass


def check_participant_joined(update: Update, context: CallbackContext) -> None:
    new_members = update.message.new_chat_members
    joined_chat_id = '%s' % update.message.chat.id

    chat = TGChat.objects.filter(tg_id=joined_chat_id).first()

    if not chat:
        return

    if not chat.is_moderated:
        return

    for new_member in new_members:
        joined_user_id = '%s' % new_member.id

        chat_user = TGChatParticipant.objects.filter(
            user__profile__telegram_id=joined_user_id,
            chat__tg_id=joined_chat_id
        ).first()

        if chat_user and chat_user.status != 'BANNED':
            chat_user.status = 'JOINED'
            chat_user.save()
            # logger.info(
            #    'User %s joined to %s %s [%s]' % (
            #        joined_user_id, update.message.chat.title, update.message.chat.title, joined_chat_id
            #    )
            # )

            if chat.chat_type == 'CHANNEL':
                context.bot.restrict_chat_member(
                    chat_id=chat.tg_id,
                    user_id=joined_user_id,
                    can_add_web_page_previews=False,
                    can_send_media_messages=False,
                    can_send_messages=False,
                    can_send_other_messages=False
                )

        else:
            existing_user = User.objects.filter(profile__telegram_id=joined_user_id).first()
            if existing_user and existing_user.is_staff:
                continue

            context.bot.kick_chat_member(chat_id=joined_chat_id, user_id=joined_user_id)
            logger.info(
                'User %s was kicked from %s %s [%s]' % (
                    joined_user_id, update.message.chat.title, update.message.chat.title, joined_chat_id
                )
            )


def check_participant_left(update: Update, context: CallbackContext) -> None:
    left_user_id = '%s' % update.message.left_chat_member.id
    left_chat_id = '%s' % update.message.chat.id
    action_by = '%s' % update.message.from_user.id

    action = 'LEFT' if action_by == left_user_id else 'BANNED'

    chat_user = TGChatParticipant.objects.filter(
        user__profile__telegram_id=left_user_id,
        chat__tg_id=left_chat_id
    ).first()

    if chat_user:
        chat_user.status = action
        chat_user.save()
        logger.info(
            'User %s has left %s %s [%s]' % (
                left_user_id, update.message.chat.title, update.message.chat.title, left_chat_id
            )
        )


def error(update, context):
    logger.warning('Update "%s" caused error "%s"' % (update, context.error))


def dialogue(update: Update, context: CallbackContext) -> None:
    update_message = update.message
    if update_message:
        if not update_message.text:
            return
        tg_user_id = update_message.from_user.id
        chat_id = update_message.chat_id
        srbc_user = User.objects.filter(profile__telegram_id=tg_user_id).first()

        if chat_id == tg_user_id:
            dialogue_message = Dialogue(
                tg_user_id=tg_user_id,
                text=update_message.text,
                is_incoming=True,
                tg_message_id=update_message.message_id
            )

            if srbc_user:
                dialogue_message.user = srbc_user

            dialogue_message.save()


def get_userinfo_by_fwd(update: Update, context: CallbackContext) -> None:
    update_message = update.message
    if update_message:
        if update_message.forward_from_chat and (not update_message.forward_from_chat.username):
            msg_text = "ID канала: *%s*" % update_message.forward_from_chat.id

            msg = context.bot.send_message(
                chat_id=update_message.chat_id,
                text=msg_text,
                reply_to_message_id=update_message.message_id,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )
        elif update_message.forward_from:
            fwd_author_tgid = update_message.forward_from.id
            fwd_author = User.objects.filter(profile__telegram_id=fwd_author_tgid).first()

            if fwd_author:
                reply_tpl = "*Instagram*: %(instagram_link)s\n" \
                            "*Профиль*: %(username)s [%(id)s](https://lk.selfreboot.camp/profile/!%(id)s/)\n" \
                            "*Статус*: %(status)s\n" \
                            "*Поток*: %(wave)s\n" \
                            "*Алярм*: %(alarm)s"

                last_ig_analysis = UserNote.objects.filter(user=fwd_author, label='IG').order_by("-date_added").first()
                last_doc_record = UserNote.objects.filter(user=fwd_author, label='DOC').order_by("-date_added").first()
                last_gtt_result = GTTResult.objects.filter(user=fwd_author).order_by("-date").first()
                last_checkpoint_photo = CheckpointPhotos.objects.filter(user=fwd_author).exclude(status='REJECTED') \
                    .order_by("-date").first()
                last_checkpoint = Checkpoint.objects.filter(user=fwd_author, is_measurements_done=True) \
                    .order_by("-date").first()

                reply_data = {
                    "id": fwd_author.pk,
                    "username": escape_markdown(fwd_author.username),
                    "status": "Активен" if fwd_author.profile.is_active else "Заблокрирован",
                    "wave": escape_markdown(fwd_author.profile.wave.title),
                    "alarm": fwd_author.profile.get_warning_flag_display(),
                }

                if last_checkpoint_photo:
                    reply_tpl += "\n*Последние контрольные фото*: %(last_checkpoint_photo_date)s"
                    reply_data['last_checkpoint_photo_date'] = last_checkpoint_photo.date.__format__('%d.%m.%Y')

                if last_checkpoint:
                    reply_tpl += "\n*Последние замеры*: %(last_checkpoint_date)s"
                    reply_data['last_checkpoint_date'] = last_checkpoint.date.__format__('%d.%m.%Y')

                if last_gtt_result:
                    reply_tpl += "\n*Результаты последнего ГТТ*: \[%(last_gtt_date)s] %(last_gtt_text)s"
                    reply_data['last_gtt_date'] = last_gtt_result.date.__format__('%d.%m.%Y')
                    reply_data['last_gtt_text'] = "\nГлюкоза: \t %.3g \t %.3g \t %.3g" \
                                                  "\nИнсулин: \t %.3g \t %.3g \t %.3g\nHOMA: %.3g" % (
                                                      last_gtt_result.glucose_0,
                                                      last_gtt_result.glucose_60,
                                                      last_gtt_result.glucose_120,
                                                      last_gtt_result.insulin_0,
                                                      last_gtt_result.insulin_60,
                                                      last_gtt_result.insulin_120,
                                                      last_gtt_result.homa_index,
                                                  )

                if last_ig_analysis:
                    reply_tpl += "\n*Последний анализ*: \[%(last_ig_date)s] %(last_ig_text)s"
                    reply_data['last_ig_date'] = last_ig_analysis.date_added.__format__('%d.%m.%Y')
                    reply_data['last_ig_text'] = escape_markdown(last_ig_analysis.content)

                if last_doc_record:
                    reply_tpl += "\n*Последня медицинская запись*: \[%(last_doc_date)s] %(last_doc_text)s"
                    reply_data['last_doc_date'] = last_doc_record.date_added.__format__('%d.%m.%Y')
                    reply_data['last_doc_text'] = escape_markdown(last_doc_record.content)

                if fwd_author.profile.instagram:
                    reply_data['instagram_link'] = '[%(instagram)s](https://instagram.com/%(instagram)s/)' % {
                        "instagram": fwd_author.profile.instagram
                    }
                else:
                    reply_data['instagram_link'] = "Не указан"

                msg_text = reply_tpl % reply_data
            else:
                msg_text = bot_messages.participant_not_familiar

            logger.info("Compiled user info: %s" % msg_text)
            if len(msg_text) < 4096:
                msg = context.bot.send_message(
                    chat_id=update.message.chat_id,
                    text=msg_text,
                    parse_mode='Markdown',
                    reply_to_message_id=update_message.message_id,
                    disable_web_page_preview=True
                )
            else:
                for x in range(0, len(msg_text), 4096):
                    msg = context.bot.send_message(
                        chat_id=update.message.chat_id,
                        text=msg_text[x:x + 4096],
                        parse_mode='Markdown',
                        reply_to_message_id=update_message.message_id,
                        disable_web_page_preview=True
                    )

            # logger.info(msg)
            store_dialogue_reply(message=msg_text, message_id=msg.message_id, tg_user_id=msg.chat_id)


def debug(update: Update, context: CallbackContext) -> None:
    logger.info('Message received: %s' % update)
    update_message = update.message
    if update_message:
        tg_user_id = update_message.from_user.id
        is_ok = False
        while not is_ok:
            try:
                User.objects.filter(profile__telegram_id=tg_user_id).first()
                is_ok = True
            except (OperationalError, InterfaceError):
                db_close()


def question_add(update: Update, context: CallbackContext) -> None:
    chat_message = update.message or update.edited_message

    if chat_message is None:
        return

    existing_message = update.edited_message is not None

    message_id = chat_message.message_id
    message_text = chat_message.text or chat_message.caption

    if message_text is None:
        return

    entities = chat_message.entities
    message_types = {
        "#вопрос": "GENERAL",
        "#сменаника": "IG",
        "#вопросыкмитингу": "MEETING",
        # u"#рацион": "MEAL",
        "#отзыв": "FEEDBACK",
        "#док": "DOC",
    }

    message_type = None
    for entity in entities:

        if entity.type != 'hashtag':
            continue
        hashtag = chat_message.text[entity.offset:entity.offset + entity.length].lower()

        if hashtag in message_types:
            message_type = message_types.get(hashtag)
            break

    if not message_type:
        return

    tg_user_id = chat_message.from_user.id

    try:
        existing_profile = Profile.objects.filter(telegram_id=tg_user_id).select_related('user').first()
    except (OperationalError, InterfaceError):
        db_close()
        existing_profile = Profile.objects.filter(telegram_id=tg_user_id).select_related('user').first()

    if not existing_profile:
        return

    message_author = existing_profile

    if existing_profile.user.is_staff:
        if message_type in ['GENERAL']:
            return

        reply_to_message = chat_message.reply_to_message

        if message_type in ['MEETING', 'DOC', 'IG', 'MEAL', 'FEEDBACK', ] and reply_to_message:
            reply_to_message_text = reply_to_message.text or reply_to_message.caption

            reply_to_profile = Profile.objects.filter(telegram_id=tg_user_id).select_related('user').first()

            if not reply_to_profile:
                return

            message_author = reply_to_profile

            message_text = "%s (Комментарий сержанта %s: %s)" % (
                reply_to_message_text,
                existing_profile.user.username,
                message_text
            )
    else:
        if message_type in ['MEETING', 'DOC']:
            return

    chat = TGChat.objects.filter(tg_id=chat_message.chat.id).first()

    if not chat:
        return

    tz = pytz.timezone(settings.TIME_ZONE)
    question = None
    if existing_message:
        question = ChatQuestion.objects.filter(message_id=message_id, chat=chat).first()

    if not question:
        question = ChatQuestion()
        question.message_id = message_id
        question.chat = chat
        question.author = message_author.user
        question.question_time = timezone.make_aware(chat_message.date, timezone=tz)

    question.question_text = message_text
    question.category = message_type

    if question.pk:
        question.save(update_fields=['question_text', 'category'])
    else:
        question.save()


def question_reply_general(update: Update, context: CallbackContext) -> None:
    chat_message = update.message or update.edited_message

    if chat_message is None:
        return

    reply_to_message = chat_message.reply_to_message

    if reply_to_message is None:
        return

    message_id = reply_to_message.message_id

    message_text = chat_message.text or chat_message.caption

    if message_text is None:
        return

    entities = reply_to_message.entities

    message_types = [
        '#вопрос'
    ]

    message_type = None
    for entity in entities:

        if entity.type != 'hashtag':
            continue
        hashtag = reply_to_message.text[entity.offset:entity.offset + entity.length].lower()

        if hashtag in message_types:
            message_type = hashtag
            break

    if not message_type:
        return

    tg_user_id = chat_message.from_user.id

    try:
        existing_profile = Profile.objects.filter(telegram_id=tg_user_id).select_related('user').first()
    except (OperationalError, InterfaceError):
        db_close()
        existing_profile = Profile.objects.filter(telegram_id=tg_user_id).select_related('user').first()

    if not existing_profile:
        return

    if not existing_profile.user.is_staff:
        return

    chat = TGChat.objects.filter(tg_id=chat_message.chat.id).first()

    if not chat:
        return

    question = ChatQuestion.objects.filter(message_id=message_id, chat=chat, category='GENERAL').first()

    if not question:
        return

    question.is_answered = True
    question.answer_text = message_text
    question.answered_time = timezone.now()
    question.answered_by = existing_profile.user
    question.save(update_fields=['is_answered', 'answer_text', 'answered_time', 'answered_by'])

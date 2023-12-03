# -*- coding: utf-8 -*-
from content.utils import store_dialogue_reply
from helpers import AttrDict

bot_messages = AttrDict()
# Служебные (staff only)
bot_messages.contact_not_found = "Нету такого. Нигде нет опечатки?"
bot_messages.contact_not_known = "С преступником Фунтиком я не знаком! (c)"
bot_messages.contact_arg_required = "Укажи имя пользователя, которого ты ищешь"
bot_messages.participant_not_familiar = "Этот участник мне не знаком. Кто здесь? 0.о"

# Техобслуживание
bot_messages.under_maintainance = "Я очень занят. Меня улучшают, а я на это смотрю и не могу оторваться. " \
                                  "Напишите попозже."
bot_messages.temporary_error = "Извините, я что-то задумался... " \
                               "Повторите своё последнее сообщение еще раз, пожалуйста?.."

# Регистрация и знакомство
bot_messages.already_registered_and_active = "Вы уже зарегистрированы. Давайте сразу к делу."
bot_messages.already_registered_but_blocked = \
    "Вы уже зарегистрированы. Но ваш аккаунт был деактивирован. \n " \
    "Пожалуйста свяжитесь с организаторами " \
    "в [\"личных сообщениях\" страницы Selfrebootcamp](https://web.facebook.com/selfrebootcamp), " \
    "чтобы выяснить в чем дело"

bot_messages.registration_phone_is_required = \
    "Для регистрации телеграм-аккаунта мне нужен номер Вашего телефона. " \
    "Нажмите прямоугольник с надписью \"Отправить боту свой номер телефона\". " \
    "Если его не видно, нажмите кнопку сбоку от поля ввода, чтобы он появился."

bot_messages.contact_confirmation_wrong_user = "Не-не-не. Мне нужен именно ВАШ номер телефона. " \
                                               "Давайте еще раз, как будто ничего не было."
bot_messages.contact_confirmation_unknown_phone_number = "Я вас не знаю. " \
                                                         "Вернитесь на сайт и укажите свой номер телефона."

# Вопросы
bot_messages.message_recorded = 'Я всё записал. Спасибо.'
bot_messages.message_recorded_response_pending = "Спасибо, вопрос записан. Ответ на него будет дан в течение суток."

bot_messages.message_accepted_away = \
    "Уведомление принято. Спасибо. " \
    "Вернувшись, сразу сообщите мне и команда откроет вам " \
    "возможность внесения рациона."

bot_messages.message_accepted_doc = \
    "Уведомление принято. Спасибо. " \
    "Ваши данные будут обработаны в даты ближайших плановых анализов."

bot_messages.message_accepted_diary = \
    "Спасибо. Дневниковая запись принята. " \
    "Мы можем не ответить на сообщение с этим тегом, " \
    "если оно не содержит прямой запрос на нашу реакцию или поддержку."

bot_messages.message_accepted_diaryprivate = \
    "Спасибо. Дневниковая запись принята. " \
    "Она никогда не будет использована в наших каналах. " \
    "Мы можем не ответить на сообщение с этим тегом, " \
    "если оно не содержит прямой запрос на нашу реакцию или поддержку."

bot_messages.no_correct_tags = \
    "Пожалуйста, снабжайте сообщения соответствующим хэштегом:\n" \
    "#формула – если вам непонятно, почему ваш рацион оцифрован именно так, как он оцифрован\n" \
    "#дневник – если хотите поблагодарить, похвастаться, поделиться своими соображениями " \
    "или переживаниями по поводу того, как протекает ваше участие в проекте.\n" \
    "Если вам нужно, чтобы дневниковое сообщение не попало в открытый доступ даже анонимно, " \
    "поставьте тег  #дневникличное\n" \
    "#вопрос – для всех остальных случаев\nСообщения с двумя и более тегами одновременно не принимаются\n\n" \
    "Внимательно читайте ответ бота на сообщение. \n\n" \
    "Правильно поставленный хэштег существенно ускорит обработку вашего сообщения командой selfREBOOTcamp."

bot_ui = AttrDict()
bot_ui.send_contact_btn = 'Отправить боту свой номер телефона'


def response_hashtags_multiple(bot, update):
    response_not_accepted(bot, update)
    msg = bot.send_message(
        chat_id=update.message.chat_id,
        text="Я не могу выбрать адресата для вашего сообщения. Пожалуйста, выберите только один тег."
    )
    # logger.info(msg)
    store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)


def response_hashtags_not_found(bot, update):
    response_not_accepted(bot, update)
    msg = bot.send_message(
        chat_id=update.message.chat_id,
        text=bot_messages.no_correct_tags
    )
    # logger.info(msg)
    store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)


def response_not_accepted(bot, update):
    msg = bot.send_message(
        chat_id=update.message.chat_id,
        text="⛔ Сообщение не принято."
    )

    # logger.info(msg)
    store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

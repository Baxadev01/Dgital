# -*- coding: utf-8 -*-

from datetime import timedelta

from django.db.models import Max
from django.utils import timezone

from content.models import TGMessage
from content.utils import store_dialogue_reply
from crm.utils.renewal import is_renewal_possible
from srbc.chatbot.messages import (
    response_not_accepted,
)


class ChatbotMessageFilter(object):
    user = None
    bot = None
    update = None
    tag = None
    message = None
    extra_args = {}
    __result__ = None
    __message__ = None
    response_message = None

    def get_result(self):
        return self.__result__

    def send_reject_response(self):
        response_not_accepted(self.bot, self.update)
        if self.response_message:
            msg = self.bot.send_message(
                chat_id=self.update.message.chat_id,
                text=self.response_message,
                parse_mode='Markdown'
            )

            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

    def __init__(self, bot, update, user, tag, **kwargs):
        self.user = user
        self.bot = bot
        self.update = update
        self.message = update.message
        self.extra_args = kwargs
        self.tag = tag

        self.do_check()
        if not self.__result__:
            self.send_reject_response()

    def do_check(self):
        raise NotImplemented


class UserCommunicationMode(ChatbotMessageFilter):
    response_message_template = "Данная функция доступна только для участников %s формата."

    default_communication_mode = 'CHANNEL'

    communication_mode_wording = {
        'CHAT': "очного",
        'CHANNEL': "заочного",
    }

    def do_check(self):
        mode_to_check = self.extra_args.get('communication_mode', self.default_communication_mode)
        communication_mode_word = self.communication_mode_wording.get(mode_to_check)

        self.response_message = self.response_message_template % communication_mode_word

        self.__result__ = self.user.profile.communication_mode == mode_to_check


class WorkDay(ChatbotMessageFilter):
    response_message = "Дорогой участник, в выходные дни мы не обрабатываем входящие сообщения. \n" \
                       "Мы с  радостью ответим на ваши вопросы и отзывы в понедельник. \n" \
                       "Для получения ответа вы можете использовать поиск в методичке, " \
                       "по доступным каналам телеграма и материалы из личного кабинета. " \
                       "В случае, если вы не нашли ответ в этих источниках - " \
                       "поступайте по инструкции из новичкового митинга: " \
                       "либо так, как делали раньше, либо так, как вам кажется правильным.\n" \
                       "В любой непонятной ситуации ешьте стейк или овощи. \n" \
                       "Мы желаем вам хороших выходных. \n\n" \
                       "Если ваш вопрос все еще будет актуальным - задайте нам его в понедельник.\n\n" \
                       "Команда selfrebootcamp"

    def do_check(self):
        now = timezone.now()
        weekday = now.weekday()
        days_since_active = (now.date() - self.user.profile.wave.start_date).days
        is_weekend = False

        if weekday == 4 and now.hour >= 19:
            is_weekend = True
        elif weekday in [5, 6]:
            is_weekend = True

        if is_weekend and days_since_active > 5:
            self.__result__ = False
        else:
            self.__result__ = True


class LimitPerDay(ChatbotMessageFilter):
    response_message_template = "Вы отправили сегодня %s сообщений с тегом \"%s\". " \
                                "Следующее сообщение с этим тегом вы сможете отправить " \
                                "через %s ч. %s мин."

    response_warning_template = "⚠️ Вы сегодня можете отправить еще одно сообщение с тегом \"%s\"."
    response_warning_last_message_template = "⚠️ Следующее сообщение с тегом \"%s\" вы сможете отправить" \
                                             " через %s ч. %s мин."
    default_limit = 5

    def do_check(self):
        message_type = self.extra_args.get('message_type')
        self.__result__ = True

        if not message_type:
            raise Exception(
                "Programming error: LimitPerDay parameter 'message_type' is missing for %s tag" % self.tag.get('tag')
            )

        yesterday_same_time = timezone.now() - timedelta(days=1)

        questions_count = TGMessage.objects.filter(
            author=self.user, message_type=message_type, created_at__gte=yesterday_same_time
        ).order_by('created_at').count()

        if not questions_count:
            return self.__result__

        limit_count = self.extra_args.get('limit', self.default_limit)
        limit_soft = self.extra_args.get('limit_soft', 0)

        if questions_count >= limit_count:
            last_questions = TGMessage.objects.filter(
                author=self.user, message_type=message_type, created_at__gte=yesterday_same_time
            ).order_by('-created_at')[:limit_count]
            first_message = list(last_questions)[-1]

            next_message_time = first_message.created_at - yesterday_same_time
            seconds_to_go = next_message_time.total_seconds() + 60
            hours_to_go = int(seconds_to_go // 3600)
            minutes_to_go = int((seconds_to_go - hours_to_go * 3600) // 60)
            hashtag_text = self.tag.get('tag').strip('#')

            self.response_message = self.response_message_template % (
                questions_count,
                hashtag_text,
                hours_to_go,
                minutes_to_go,
            )

            self.__result__ = False
        elif questions_count == limit_count - 2:
            hashtag_text = self.tag.get('tag').strip('#')
            warning_message = self.response_warning_template % (
                hashtag_text,
            )
            msg = self.bot.send_message(
                chat_id=self.update.message.chat_id,
                text=warning_message,
                parse_mode='Markdown'
            )

            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)
        elif questions_count == limit_count - 1:
            last_questions = TGMessage.objects.filter(
                author=self.user, message_type=message_type, created_at__gte=yesterday_same_time
            ).order_by('-created_at')[:limit_count-1]

            first_message = list(last_questions)[-1]

            next_message_time = first_message.created_at - yesterday_same_time
            seconds_to_go = next_message_time.total_seconds() + 60
            hours_to_go = int(seconds_to_go // 3600)
            minutes_to_go = int((seconds_to_go - hours_to_go * 3600) // 60)

            hashtag_text = self.tag.get('tag').strip('#')
            warning_message = self.response_warning_last_message_template % (
                hashtag_text,
                hours_to_go,
                minutes_to_go,
            )
            msg = self.bot.send_message(
                chat_id=self.update.message.chat_id,
                text=warning_message,
                parse_mode='Markdown'
            )

            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

        return self.__result__


class MessageLength(ChatbotMessageFilter):
    response_message = "Пожалуйта, пишите сообщение полностью. И не забудьте указать необходимый хэштег."
    default_limit = 20

    def do_check(self):
        self.__result__ = len("%s" % self.message.text.strip()) >= self.extra_args.get('min', self.default_limit)


class FloodControl(ChatbotMessageFilter):
    response_message = "Следующее сообщение я могу принять не ранее, чем через минуту."
    default_timeout = 60

    def do_check(self):
        message_type = self.extra_args.get('message_type')
        self.__result__ = True

        if not message_type:
            raise Exception(
                "Programming error: Flood control parameter 'message_type' is missing for %s tag" % self.tag.get('tag')
            )

        last_my_question = TGMessage.objects \
            .filter(author=self.user, message_type=message_type) \
            .aggregate(last_message=Max('created_at')).get('last_message')

        if not last_my_question:
            return self.__result__

        timeout_seconds = self.extra_args.get('timeout', self.default_timeout)

        if last_my_question + timedelta(seconds=timeout_seconds) > timezone.localtime():
            self.__result__ = False

        return self.__result__


class RenewalIsPossible(ChatbotMessageFilter):
    def do_check(self):
        renewal_possible, rejection_reason = is_renewal_possible(self.user)
        self.__result__ = renewal_possible

        if not self.__result__:
            self.response_message = rejection_reason

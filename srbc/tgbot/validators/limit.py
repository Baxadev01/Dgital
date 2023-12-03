# -*- coding: utf-8 -*-
from datetime import timedelta

from django.utils import timezone

from content.models import TGMessage
from srbc.tgbot.actions import SendMessage
from srbc.tgbot.config import NodeTranslations
from srbc.tgbot.models import TGBotValidator
from srbc.tgbot.utils import translate as _

__all__ = ('LimitPerDay',)

Q_MESSAGE_TYPES = [TGMessage.TYPE_QUESTION, TGMessage.TYPE_FORMULA, TGMessage.TYPE_MEAL]


class LimitPerDay(TGBotValidator):

    def __init__(self, limit_amount=5):
        self.limit_amount = limit_amount

    def is_valid(self, node):
        user = node.get_user()
        yesterday_same_time = timezone.now() - timedelta(days=1)
        questions_count = TGMessage.objects.filter(
            author=user, message_type__in=Q_MESSAGE_TYPES, created_at__gte=yesterday_same_time
        ).order_by('created_at').count()

        if not questions_count:
            return True

        response_message_template = _(NodeTranslations.LIMIT_PER_DAY_VALIDATION_FAILED__TXT)

        if questions_count >= self.limit_amount:
            last_questions = TGMessage.objects.filter(
                author=user, message_type__in=Q_MESSAGE_TYPES, created_at__gte=yesterday_same_time
            ).order_by('-created_at')[:self.limit_amount]
            first_message = list(last_questions)[-1]

            next_message_time = first_message.created_at - yesterday_same_time
            seconds_to_go = next_message_time.total_seconds() + 60
            hours_to_go = int(seconds_to_go // 3600)
            minutes_to_go = int((seconds_to_go - hours_to_go * 3600) // 60)

            response_message_template = response_message_template.format(
                questions_count=questions_count,
                hours=hours_to_go,
                minutes=minutes_to_go
            )

            prev_node_data = node.get_prev_node_data()
            self._failure_actions = [
                SendMessage(messages=[response_message_template],
                            keyboard=prev_node_data['keyboard'])
            ]
            return False

        else:
            return True

# -*- coding: utf-8 -*-

from datetime import timedelta

from django.utils import timezone

from content.models import TGMessage
from srbc.tgbot.config import NodeTranslations
from srbc.tgbot.models import TGBotAction
from srbc.tgbot.utils import translate as _
from .send_message import SendMessage

__all__ = ('LimitPerDayNotification', )

Q_MESSAGE_TYPES = [TGMessage.TYPE_QUESTION, TGMessage.TYPE_FORMULA, TGMessage.TYPE_MEAL]


class LimitPerDayNotification(TGBotAction):

    def __init__(self, limit_amount=5):
        """
        :type limit_amount: int
        """
        super(LimitPerDayNotification, self).__init__()
        self.limit_amount = limit_amount

    def execute(self, node):
        """
        :type node: srbc.tgbot.models.TGBotNode
        """
        user = node.get_user()
        prev_node_data = node.get_prev_node_data()

        yesterday_same_time = timezone.now() - timedelta(days=1)
        questions_count = TGMessage.objects.filter(
            author=user, message_type__in=Q_MESSAGE_TYPES, created_at__gte=yesterday_same_time
        ).order_by('created_at').count()

        if not questions_count:
            return

        if questions_count == (self.limit_amount - 1):
            SendMessage(messages=[_(NodeTranslations.LIMIT_PER_DAY_WARNING__TXT)],
                        keyboard=prev_node_data['keyboard']).execute(node=node)

        elif questions_count == self.limit_amount:
            msg_template = _(NodeTranslations.LIMIT_PER_DAY_LAST_MESSAGE__TXT)
            last_questions = TGMessage.objects.filter(
                author=user, message_type__in=Q_MESSAGE_TYPES, created_at__gte=yesterday_same_time
            ).order_by('-created_at')[:self.limit_amount - 1]

            first_message = list(last_questions)[-1]

            next_message_time = first_message.created_at - yesterday_same_time
            seconds_to_go = next_message_time.total_seconds() + 60
            hours_to_go = int(seconds_to_go // 3600)
            minutes_to_go = int((seconds_to_go - hours_to_go * 3600) // 60)

            msg = msg_template.format(
                hours=hours_to_go, minutes=minutes_to_go
            )

            SendMessage(messages=[msg], keyboard=prev_node_data['keyboard']).execute(node=node)

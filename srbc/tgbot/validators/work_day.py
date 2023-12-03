# -*- coding: utf-8 -*-
from django.utils import timezone

from srbc.tgbot.actions import SendMessage
from srbc.tgbot.config import NodeTranslations
from srbc.tgbot.models import TGBotValidator
from srbc.tgbot.utils import translate as _

__all__ = ('WorkDay',)


class WorkDay(TGBotValidator):

    def is_valid(self, node):
        user = node.get_user()
        prev_node_data = node.get_prev_node_data()

        now = timezone.now()
        weekday = now.weekday()
        if user.profile.wave:
            days_since_active = (now.date() - user.profile.wave.start_date).days
        else:
            # Заглушка от поступенцев
            days_since_active = 99

        is_weekend = False
        if weekday == 4 and now.hour >= 19:
            is_weekend = True
        elif weekday in [5, 6]:
            is_weekend = True

        if is_weekend and (days_since_active > 5):
            self._failure_actions = [
                SendMessage(messages=[_(NodeTranslations.WORK_DAY_VALIDATION_FAILED__TXT)],
                            keyboard=prev_node_data['keyboard'])
            ]
            return False
        else:
            return True

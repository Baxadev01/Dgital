# -*- coding: utf-8 -*-
from datetime import timedelta

from django.db.models import Max
from django.utils import timezone

from content.models import TGMessage
from srbc.tgbot.actions import SendMessage
from srbc.tgbot.config import NodeTranslations
from srbc.tgbot.models import TGBotValidator
from srbc.tgbot.utils import translate as _

__all__ = ('FloodControl',)


class FloodControl(TGBotValidator):

    def __init__(self, message_type, timeout=60):
        self.message_type = message_type
        self.timeout = timeout

    def is_valid(self, node):
        user = node.get_user()
        prev_node_data = node.get_prev_node_data()

        last_my_question = TGMessage.objects.\
            filter(author=user, message_type=self.message_type).\
            aggregate(last_message=Max('created_at')).\
            get('last_message')

        if not last_my_question:
            return True

        if (last_my_question + timedelta(seconds=self.timeout)) > timezone.localtime():
            self._failure_actions = [
                SendMessage(messages=[_(NodeTranslations.FLOOD_CONTROL_VALIDATION_FAILED__TXT)],
                            keyboard=prev_node_data['keyboard'])
            ]
            return False
        else:
            return True

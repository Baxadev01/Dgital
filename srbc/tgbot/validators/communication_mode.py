# -*- coding: utf-8 -*-
from srbc.tgbot.actions import SendMessage
from srbc.tgbot.config import NodeTranslations
from srbc.tgbot.models import TGBotValidator
from srbc.tgbot.utils import translate as _

__all__ = ('CommunicationMode',)


class CommunicationMode(TGBotValidator):
    TYPE_CHANNEL = 'CHANNEL'
    TYPE_CHAT = 'CHAT'
    TYPE_ANY = 'ALL'

    def __init__(self, communication_type):
        self.communication_type = communication_type

    def is_valid(self, node):
        user = node.get_user()
        prev_node_data = node.get_prev_node_data()

        has_access = False

        if self.communication_type == self.TYPE_ANY:
            # сделал так - это поле может быть None, и не можем просто тут всегда True
            if user.profile.communication_mode:
                has_access = True

        elif user.profile.communication_mode == self.communication_type:
            has_access = True

        if not has_access:
            self._failure_actions = [
                SendMessage(messages=[_(NodeTranslations.COMMUNICATION_MODE_VALIDATION_FAILED__TXT)],
                            keyboard=prev_node_data['keyboard'])
            ]

        return has_access

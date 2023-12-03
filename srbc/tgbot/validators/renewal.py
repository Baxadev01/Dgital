# -*- coding: utf-8 -*-

from crm.utils.renewal import is_renewal_possible
from srbc.tgbot.actions import SendMessage
from srbc.tgbot.models import TGBotValidator

__all__ = ('RenewalIsPossible',)


class RenewalIsPossible(TGBotValidator):

    def is_valid(self, node):
        # TODO: update rejection_reasons according to new chat bot
        renewal_possible, rejection_reason = is_renewal_possible(node.get_user())
        if renewal_possible:
            return True

        prev_node_data = node.get_prev_node_data()
        self._failure_actions = [
            SendMessage(messages=[rejection_reason], keyboard=prev_node_data['keyboard'])
        ]
        return False

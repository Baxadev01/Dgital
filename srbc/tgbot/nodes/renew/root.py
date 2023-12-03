# -*- coding: utf-8 -*-

from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import CommunicationMode, RenewalIsPossible

__all__ = ('RenewNode', 'RenewRouterNode')


@bot_manager.register(key=NodeNames.RENEW)
class RenewNode(BaseNode):
    validators = [
        CommunicationMode(communication_type=CommunicationMode.TYPE_ANY),
        RenewalIsPossible()
    ]

    def get_messages(self):
        return [_(NodeTranslations.RENEW__TXT)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.RENEW_CONT)],
            [TGRB(NodeNames.RENEW_STOP)],
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.RENEW_ROUTER)
class RenewRouterNode(RouterNode):
    pass

# -*- coding: utf-8 -*-

from srbc.tgbot.actions import GoToNode, DefaultSendMessages, GoToChosenNodeOrGoToNode, ProcessRenewalRequest
from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode, BaseEndNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import TextInput, ChooseNodeOrGoNextNode, RenewalIsPossible

__all__ = ('RenewContNode', 'RenewContRouterNode', 'RenewContInputNode')


@bot_manager.register(key=NodeNames.RENEW_CONT)
class RenewContNode(BaseNode):
    validators = [
        RenewalIsPossible()
    ]

    def get_messages(self):
        return [_(NodeTranslations.RENEW_CONT__TXT)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.RENEW_CONT_ROUTER)
class RenewContRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.RENEW_CONT_INPUT)]


@bot_manager.register(key=NodeNames.RENEW_CONT_INPUT)
class RenewContInputNode(BaseEndNode):
    validators = [
        RenewalIsPossible(),
        TextInput()
    ]
    
    handlers = [
        ProcessRenewalRequest(stop_renewal=False),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.MAIN_MENU_ROUTER)
    ]

    def get_messages(self):
        return [_(NodeTranslations.RENEW_CONT__SAVE_OK)]

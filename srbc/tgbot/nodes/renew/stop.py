# -*- coding: utf-8 -*-

from srbc.tgbot.actions import GoToNode, DefaultSendMessages, ProcessRenewalRequest, GoToChosenNodeOrGoToNode
from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode, BaseEndNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import TextInput, ChooseNodeOrGoNextNode, RenewalIsPossible

__all__ = ('RenewStopNode', 'RenewStopRouterNode', 'RenewStopInputNode')


@bot_manager.register(key=NodeNames.RENEW_STOP)
class RenewStopNode(BaseNode):
    validators = [
        RenewalIsPossible()
    ]

    def get_messages(self):
        return [_(NodeTranslations.RENEW_STOP__TXT)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.RENEW_STOP_ROUTER)
class RenewStopRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.RENEW_STOP_INPUT)]


@bot_manager.register(key=NodeNames.RENEW_STOP_INPUT)
class RenewStopInputNode(BaseEndNode):
    validators = [
        RenewalIsPossible(),
        TextInput()
    ]
    
    handlers = [
        ProcessRenewalRequest(stop_renewal=True),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.MAIN_MENU_ROUTER)
    ]

    def get_messages(self):
        return [_(NodeTranslations.RENEW_STOP__SAVE_OK)]

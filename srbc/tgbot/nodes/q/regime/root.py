# -*- coding: utf-8 -*-

from srbc.tgbot.actions import GoToNode, DefaultSendMessages, SaveTGMessage, GoToChosenNodeOrGoToNode, \
    LimitPerDayNotification, TimeoutRedirect
from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode, BaseEndNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import TextInput, ChooseNodeOrGoNextNode, WorkDay, FloodControl, LimitPerDay

__all__ = ('QRegimeNode', 'QRegimeRouterNode', 'QRegimeInputNode')


@bot_manager.register(key=NodeNames.Q_REGIME)
class QRegimeNode(BaseNode):
    validators = [
        WorkDay(),
        FloodControl(message_type=SaveTGMessage.TYPE_MEAL),
        LimitPerDay()
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_REGIME__TXT)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.Q_REGIME_ROUTER)
class QRegimeRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.Q_REGIME_INPUT)]


@bot_manager.register(key=NodeNames.Q_REGIME_INPUT)
class QRegimeInputNode(BaseEndNode):
    validators = [TextInput()]
    handlers = [
        TimeoutRedirect(),
        SaveTGMessage(message_type=SaveTGMessage.TYPE_MEAL),
        LimitPerDayNotification(),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.MAIN_MENU_ROUTER)
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_REGIME__SAVE_OK)]

# -*- coding: utf-8 -*-

from srbc.tgbot.actions import GoToNode, DefaultSendMessages, SaveTGMessage, GoToChosenNodeOrGoToNode, PreSaveMessage, \
    LimitPerDayNotification
from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode, BaseEndNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import TextInput, ChooseNodeOrGoNextNode, WorkDay, FloodControl, LimitPerDay

__all__ = ('QAnlzdietNode', 'QAnlzdietRouterNode',
           'QAnlzdietInputNode', 'QAnlzdietInputRouterNode',
           'QAnlzdietQuestionInputNode')


@bot_manager.register(key=NodeNames.Q_ANLZDIET)
class QAnlzdietNode(BaseNode):
    validators = [
        WorkDay(),
        FloodControl(message_type=SaveTGMessage.TYPE_FORMULA),
        LimitPerDay()
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_ANLZDIET__TXT)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.Q_ANLZDIET_ROUTER)
class QAnlzdietRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.Q_ANLZDIET_INPUT)]


@bot_manager.register(key=NodeNames.Q_ANLZDIET_INPUT)
class QAnlzdietInputNode(BaseNode):
    validators = [TextInput()]
    handlers = [
        PreSaveMessage(),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.Q_ANLZDIET_INPUT_ROUTER)
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_ANLZDIET__SAVE_OK_1)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.Q_ANLZDIET_INPUT_ROUTER)
class QAnlzdietInputRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.Q_ANLZDIET_QUESTION_INPUT)]


@bot_manager.register(key=NodeNames.Q_ANLZDIET_QUESTION_INPUT)
class QAnlzdietQuestionInputNode(BaseEndNode):
    validators = [TextInput()]
    handlers = [
        SaveTGMessage(message_type=SaveTGMessage.TYPE_FORMULA),
        LimitPerDayNotification(),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.BACK_TO_MAIN_MENU)
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_ANLZDIET__SAVE_OK_2)]

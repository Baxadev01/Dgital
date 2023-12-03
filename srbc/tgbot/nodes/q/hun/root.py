# -*- coding: utf-8 -*-
from srbc.tgbot.actions import GoToNode, DefaultSendMessages, SaveTGMessage, GoToChosenNodeOrGoToNode, PreSaveMessage, \
    LimitPerDayNotification, TimeoutRedirect
from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode, BaseEndNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import TextInput, ChooseNodeOrGoNextNode, WorkDay, FloodControl, LimitPerDay

__all__ = ('QHUNNode', 'QHUNRouterNode', 'QHUNInputNode', 'QHUNInputRouterNode', 'QHUNQuestionInputNode')


@bot_manager.register(key=NodeNames.Q_HUN)
class QHUNNode(BaseNode):
    validators = [
        WorkDay(),
        FloodControl(message_type=SaveTGMessage.TYPE_MEAL),
        LimitPerDay()
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_HUN__TXT)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.Q_HUN_ROUTER)
class QHUNRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.Q_HUN_INPUT)]


@bot_manager.register(key=NodeNames.Q_HUN_INPUT)
class QHUNInputNode(BaseNode):
    validators = [TextInput()]
    handlers = [
        PreSaveMessage(),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.Q_HUN_INPUT_ROUTER)
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_HUN__SAVE_OK_1)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.Q_HUN_INPUT_ROUTER)
class QHUNInputRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.Q_HUN_QUESTION_INPUT)]


@bot_manager.register(key=NodeNames.Q_HUN_QUESTION_INPUT)
class QHUNQuestionInputNode(BaseEndNode):
    validators = [TextInput(min_length=4)]
    handlers = [
        TimeoutRedirect(),
        SaveTGMessage(message_type=SaveTGMessage.TYPE_MEAL),
        LimitPerDayNotification(),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.BACK_TO_MAIN_MENU)
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_HUN__SAVE_OK_2)]

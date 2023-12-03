# -*- coding: utf-8 -*-
from srbc.tgbot.actions import GoToNode, DefaultSendMessages, SaveTGMessage, GoToChosenNodeOrGoToNode, PreSaveMessage, \
    LimitPerDayNotification, TimeoutRedirect
from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode, BaseEndNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import TextInput, ChooseNodeOrGoNextNode

__all__ = ('QOrgDietNowNode', 'QOrgDietNowRouterNode', 'QOrgDietNowInputNode', 'QOrgDietNowInputRouterNode',
           'QOrgDietNowQuestionInputNode')


@bot_manager.register(key=NodeNames.Q_ORGDIET_NOW)
class QOrgDietNowNode(BaseNode):

    def get_messages(self):
        return [_(NodeTranslations.Q_ORGDIET_NOW__TXT1)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.Q_ORGDIET_NOW_ROUTER)
class QOrgDietNowRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.Q_ORGDIET_NOW_INPUT)]


@bot_manager.register(key=NodeNames.Q_ORGDIET_NOW_INPUT)
class QOrgDietNowInputNode(BaseNode):
    validators = [TextInput()]
    handlers = [
        PreSaveMessage(),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.Q_ORGDIET_NOW_INPUT_ROUTER)
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_ORGDIET_NOW__TXT2)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.Q_ORGDIET_NOW_INPUT_ROUTER)
class QOrgDietNowInputRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.Q_ORGDIET_NOW_QUESTION_INPUT)]


@bot_manager.register(key=NodeNames.Q_ORGDIET_NOW_QUESTION_INPUT)
class QOrgDietNowQuestionInputNode(BaseEndNode):
    validators = [TextInput()]
    handlers = [
        TimeoutRedirect(),
        SaveTGMessage(message_type=SaveTGMessage.TYPE_MEAL),
        LimitPerDayNotification(),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.BACK_TO_MAIN_MENU)
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_ORGDIET__SAVE_OK)]

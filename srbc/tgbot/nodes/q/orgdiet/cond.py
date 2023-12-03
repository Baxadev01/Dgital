# -*- coding: utf-8 -*-

from srbc.tgbot.actions import GoToNode, DefaultSendMessages, SaveTGMessage, GoToChosenNodeOrGoToNode, \
    LimitPerDayNotification, TimeoutRedirect
from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode, BaseEndNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import TextInput, ChooseNodeOrGoNextNode

__all__ = ('QOrgDietCondNode', 'QOrgDietCondRouterNode', 'QOrgDietCondQuestionInputNode')


@bot_manager.register(key=NodeNames.Q_ORGDIET_COND)
class QOrgDietCondNode(BaseNode):

    def get_messages(self):
        return [_(NodeTranslations.Q_ORGDIET_COND__TXT)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.Q_ORGDIET_COND_ROUTER)
class QOrgDietCondRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.Q_ORGDIET_COND_QUESTION_INPUT)]


@bot_manager.register(key=NodeNames.Q_ORGDIET_COND_QUESTION_INPUT)
class QOrgDietCondQuestionInputNode(BaseEndNode):
    validators = [TextInput()]
    handlers = [
        TimeoutRedirect(),
        SaveTGMessage(message_type=SaveTGMessage.TYPE_MEAL),
        LimitPerDayNotification(),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.MAIN_MENU_ROUTER)
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_ORGDIET__SAVE_OK)]

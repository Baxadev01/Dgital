# -*- coding: utf-8 -*-

from srbc.tgbot.actions import GoToNode, DefaultSendMessages, SaveTGMessage, \
    GoToChosenNodeOrGoToNode, TimeoutRedirect
from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode, BaseEndNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import TextInput, ChooseNodeOrGoNextNode

__all__ = ('DiaryPublicNode', 'DiaryPublicRouterNode', 'DiaryPublicInputNode')


@bot_manager.register(key=NodeNames.DIARY_PUBLIC)
class DiaryPublicNode(BaseNode):

    def get_messages(self):
        return [_(NodeTranslations.DIARY_PUBLIC__TXT)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.DIARY_PUBLIC_ROUTER)
class DiaryPublicRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.DIARY_PUBLIC_INPUT)]


@bot_manager.register(key=NodeNames.DIARY_PUBLIC_INPUT)
class DiaryPublicInputNode(BaseEndNode):
    validators = [TextInput()]
    handlers = [
        TimeoutRedirect(),
        SaveTGMessage(message_type=SaveTGMessage.TYPE_FEEDBACK),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.MAIN_MENU_ROUTER)
    ]

    def get_messages(self):
        return [_(NodeTranslations.DIARY_PUBLIC__SAVE_OK)]

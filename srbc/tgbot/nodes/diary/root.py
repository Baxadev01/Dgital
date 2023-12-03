# -*- coding: utf-8 -*-

from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import CommunicationMode, WorkDay

__all__ = ('DiaryNode', 'DiaryRouterNode')


@bot_manager.register(key=NodeNames.DIARY)
class DiaryNode(BaseNode):
    validators = [
        CommunicationMode(communication_type=CommunicationMode.TYPE_ANY),
        WorkDay()
    ]

    def get_messages(self):
        return [_(NodeTranslations.DIARY__TXT)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.DIARY_PUBLIC)],
            [TGRB(NodeNames.DIARY_NOTPUBLIC)],
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.DIARY_ROUTER)
class DiaryRouterNode(RouterNode):
    pass

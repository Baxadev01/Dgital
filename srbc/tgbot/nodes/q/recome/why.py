# -*- coding: utf-8 -*-

from srbc.tgbot.actions import DefaultSendMessages, GoToNode
from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames
from srbc.tgbot.config import NodeTranslations
from srbc.tgbot.nodes.base import BaseNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from .utils import get_keyboard as get_general_keyboard

__all__ = ('QRecomWhyNode',)


@bot_manager.register(key=NodeNames.Q_RECOM_WHY)
class QRecomWhyNode(BaseNode):
    handlers = [
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.Q_RECOM_ROUTER)
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_RECOM_WHY__TXT)]

    def get_keyboard(self):
        return get_general_keyboard(self.get_user())

# -*- coding: utf-8 -*-

from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from .utils import get_keyboard as get_general_keyboard

__all__ = ('QRecomNode', 'QRecomRouterNode')


@bot_manager.register(key=NodeNames.Q_RECOM)
class QRecomNode(BaseNode):
    def get_messages(self):
        return [_(NodeTranslations.Q_RECOM__TXT)]

    def get_keyboard(self):
        return get_general_keyboard(self.get_user())


@bot_manager.register(key=NodeNames.Q_RECOM_ROUTER)
class QRecomRouterNode(RouterNode):
    pass

# -*- coding: utf-8 -*-

from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseEndNode
from srbc.tgbot.utils import translate as _

__all__ = ('QDataNode',)


@bot_manager.register(key=NodeNames.Q_DATA)
class QDataNode(BaseEndNode):

    def get_messages(self):
        return [_(NodeTranslations.Q_DATA__TXT)]

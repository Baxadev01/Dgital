# -*- coding: utf-8 -*-

from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseEndNode
from srbc.tgbot.utils import translate as _

__all__ = ('QTechYesNode',)


@bot_manager.register(key=NodeNames.Q_TECH_YES)
class QTechYesNode(BaseEndNode):

    def get_messages(self):
        return [_(NodeTranslations.Q_TECH_YES__TXT)]

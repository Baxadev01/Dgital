# -*- coding: utf-8 -*-

from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import WorkDay, FloodControl, LimitPerDay
from srbc.tgbot.actions import SaveTGMessage


__all__ = ('QOrgDietNode', 'QOrgDietRouterNode')


@bot_manager.register(key=NodeNames.Q_ORGDIET)
class QOrgDietNode(BaseNode):
    validators = [
        WorkDay(),
        FloodControl(message_type=SaveTGMessage.TYPE_MEAL),
        LimitPerDay()
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_ORGDIET__TXT)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.Q_ORGDIET_NOW), TGRB(NodeNames.Q_ORGDIET_COND)],
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.Q_ORGDIET_ROUTER)
class QOrgDietRouterNode(RouterNode):
    pass

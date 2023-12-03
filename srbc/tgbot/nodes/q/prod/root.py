# -*- coding: utf-8 -*-

from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _

__all__ = ('QProdNode', 'QProdRouterNode')


@bot_manager.register(key=NodeNames.Q_PROD)
class QProdNode(BaseNode):
    def get_messages(self):
        user = self.get_user()
        if user.profile.has_full_bot_access:
            return [_(NodeTranslations.Q_PROD__TXT_1), _(NodeTranslations.Q_PROD__TXT_2)]

        return [_(NodeTranslations.Q_PROD__TXT_NO_QUESTIONS_TARIFF)]

    def get_keyboard(self):
        user = self.get_user()
        if user.profile.has_full_bot_access:
            return [
                [TGRB(NodeNames.Q_PROD_YES), TGRB(NodeNames.Q_PROD_NO)],
                [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
            ]

        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.Q_PROD_ROUTER)
class QProdRouterNode(RouterNode):
    pass

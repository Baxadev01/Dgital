# -*- coding: utf-8 -*-

from django.utils import timezone

from srbc.tgbot.bot import bot_manager
from srbc.tgbot.actions import GoToNodeByTernaryOperator
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import CommunicationMode

__all__ = ('QBaseNode', 'QNode', 'QRouterNode')


@bot_manager.register(key=NodeNames.Q_BASE)
class QBaseNode(BaseNode):

    def __init__(self, bot, update, user=None, tg_user_id=None, prev_node_data=None):
        super(QBaseNode, self).__init__(bot, update, user, tg_user_id, prev_node_data)
        self.validators = [
        ]
        self.handlers = [
            GoToNodeByTernaryOperator(
                ternary_function=self.check_access,
                node_key_true=NodeNames.Q_NOTHING_FOUND,
                node_key_false=NodeNames.Q
            )
        ]

    def check_access(self):
        # при заходе в ветку "задать вопрос" показываем
        # 1. для пользователей с полным доступом
        #  - первые 28 дней только прямое задавание вопроса
        #   - потом все меню
        # 2. для пользователей с базовым доступом всегда укороченное меню с базовыми ответами
        user = self.get_user()
        if not user.profile.has_full_bot_access:
            return False
        else:
            now = timezone.now()
            days_since_start = (now.date() - user.profile.wave.start_date).days
            return days_since_start < 28

    def get_messages(self):
        return None

    def get_keyboard(self):
        return None


@bot_manager.register(key=NodeNames.Q)
class QNode(BaseNode):
    validators = [
        CommunicationMode(communication_type=CommunicationMode.TYPE_ANY),
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q__TXT)]

    def get_keyboard(self):
        # чтобы не делать разные узлы - тут тоже придется добавить проверку и строить меню в зависимости от этого
        user = self.get_user()
        if user.profile.has_full_bot_access:
            return [
                [TGRB(NodeNames.Q_TECH)],
                [TGRB(NodeNames.Q_PROD)],
                [TGRB(NodeNames.Q_DATA)],
                [TGRB(NodeNames.Q_ANLZDIET)],
                [TGRB(NodeNames.Q_THR)],
                [TGRB(NodeNames.Q_HUN)],
                [TGRB(NodeNames.Q_LRGPORT)],
                [TGRB(NodeNames.Q_ORGDIET)],
                [TGRB(NodeNames.Q_REGIME)],
                [TGRB(NodeNames.Q_RECOM)],
                [TGRB(NodeNames.Q_NOTHING_FOUND)],
                [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
            ]
        else:
            return [
                [TGRB(NodeNames.Q_TECH)],
                [TGRB(NodeNames.Q_PROD)],
                [TGRB(NodeNames.Q_DATA)],
                [TGRB(NodeNames.Q_LRGPORT)],
                [TGRB(NodeNames.Q_RECOM)],
                [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
            ]


@bot_manager.register(key=NodeNames.Q_ROUTER)
class QRouterNode(RouterNode):
    pass

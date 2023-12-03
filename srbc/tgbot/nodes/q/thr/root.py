# -*- coding: utf-8 -*-

from django.utils import timezone

from srbc.tgbot.actions import GoToNode, GoToNodeByTernaryOperator, GoToChosenNodeOrGoToNode, \
    SaveTGMessage, DefaultSendMessages, LimitPerDayNotification, TimeoutRedirect
from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseEndNode, BaseNode, RouterNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import ChooseNodeOrGoNextNode
from srbc.tgbot.validators import TextInput, WorkDay, FloodControl, LimitPerDay

__all__ = ('QTHRNode', 'QTHRTrueNode', 'QTHRFalseNode', 'QTHRFalseRouterNode', 'QTHRFalseInputNode')


@bot_manager.register(key=NodeNames.Q_THR)
class QTHRNode(BaseNode):

    def __init__(self, bot, update, user=None, tg_user_id=None, prev_node_data=None):
        super(QTHRNode, self).__init__(bot, update, user, tg_user_id, prev_node_data)
        self.validators = [
            WorkDay(),
            FloodControl(message_type=SaveTGMessage.TYPE_QUESTION),
            LimitPerDay()
        ]
        self.handlers = [
            GoToNodeByTernaryOperator(
                ternary_function=self.check_days_since_start,
                node_key_true=NodeNames.Q_THR_TRUE,
                node_key_false=NodeNames.Q_THR_FALSE
            )
        ]

    def check_days_since_start(self):
        user = self.get_user()
        now = timezone.now()
        days_since_start = (now.date() - user.profile.wave.start_date).days
        return days_since_start < 56

    def get_messages(self):
        return None

    def get_keyboard(self):
        return None


@bot_manager.register(key=NodeNames.Q_THR_TRUE)
class QTHRTrueNode(BaseEndNode):

    def get_messages(self):
        return [_(NodeTranslations.Q_THR__TXT1)]


@bot_manager.register(key=NodeNames.Q_THR_FALSE)
class QTHRFalseNode(BaseNode):

    def get_messages(self):
        return [_(NodeTranslations.Q_THR__TXT2)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.Q_THR_FALSE_ROUTER)
class QTHRFalseRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.Q_THR_FALSE_INPUT)]


@bot_manager.register(key=NodeNames.Q_THR_FALSE_INPUT)
class QTHRFalseInputNode(BaseEndNode):
    validators = [TextInput()]
    handlers = [
        TimeoutRedirect(),
        SaveTGMessage(message_type=SaveTGMessage.TYPE_QUESTION),
        LimitPerDayNotification(),
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.MAIN_MENU_ROUTER)
    ]

    def get_messages(self):
        return [_(NodeTranslations.Q_THR__SAVE_OK)]

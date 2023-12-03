# -*- coding: utf-8 -*-

import abc

from srbc.tgbot.actions import GoToChosenNode, GoToRouterNode, DefaultSendMessages, GoToNode
from srbc.tgbot.config import NodeNames
from srbc.tgbot.models import TGBotNode
from srbc.tgbot.utils import TGRouterButton as TGRB
from srbc.tgbot.validators import ChooseNode


class BaseNode(TGBotNode):
    """
    Базовая нода для вывода:
        1) сообщения
        2) клавиатуры
        3) перевода в ноду-роутер (которая на основании нажатой кнопки переходит в нужную ноду)
    Ноды, которые наследуются от этой, в общем случае, определяют всего лишь методы get_messages и get_keyboard.
    """
    auto_processing = True

    validators = []
    handlers = [
        DefaultSendMessages(),
        GoToRouterNode()
    ]

    def __init__(self, bot, update, user=None, tg_user_id=None, prev_node_data=None):
        super(BaseNode, self).__init__(bot, update, user, tg_user_id, prev_node_data)

    @abc.abstractmethod
    def get_messages(self):
        pass

    @abc.abstractmethod
    def get_keyboard(self):
        pass


class RouterNode(TGBotNode):
    """
    Базовая нода-роутер.
    Принцип работы такой:
    - нода-роутер ждет входящего сообщения от пользователя
    - если нажали на кнопку клавиатуры, то переходит в необходимую ноду

    Ноды, которые наследуются от этой, в общем случае, ничего не определяют.
    """
    auto_processing = False

    validators = [ChooseNode()]
    handlers = [GoToChosenNode()]

    def __init__(self, bot, update, user=None, tg_user_id=None, prev_node_data=None):
        super(RouterNode, self).__init__(bot, update, user, tg_user_id, prev_node_data)

    def get_messages(self):
        return None

    def get_keyboard(self):
        return None


class BaseEndNode(BaseNode):
    """
    Базовая нода завершения алгоритма и возврата в Главное Меню.
    В общем случае используется в нодах - концах дерева.
    """
    handlers = [
        DefaultSendMessages(),
        GoToNode(node_key=NodeNames.MAIN_MENU_ROUTER)
    ]

    @abc.abstractmethod
    def get_messages(self):
        pass

    def get_keyboard(self):
        user = self.get_user()
        if user.profile.has_full_bot_access:
            return [
                [TGRB(NodeNames.Q_BASE)],
                [TGRB(NodeNames.NODATA)],
                [TGRB(NodeNames.DOC)],
                [TGRB(NodeNames.RENEW)],
                [TGRB(NodeNames.DIARY)],
            ]
        else:
            return [
                [TGRB(NodeNames.Q_BASE)],
                [TGRB(NodeNames.NODATA)],
                [TGRB(NodeNames.DOC)],
                [TGRB(NodeNames.RENEW)],
            ]

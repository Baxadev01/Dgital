# -*- coding: utf-8 -*-
from datetime import datetime
from django.conf import settings
from srbc.tgbot.models import TGBotAction
from srbc.tgbot.config import NodeNames

__all__ = ('GoToNode', 'GoToChosenNode', 'GoToRouterNode',
           'GoToChosenNodeOrGoToNode', 'GoToNodeByTernaryOperator', 'TimeoutRedirect')


class GoToNode(TGBotAction):
    """
    Переход в определнную ноду.
    """
    node_key = None

    def __init__(self, node_key):
        """
        :type node_key: basestring
        """
        super(GoToNode, self).__init__()
        self.node_key = node_key

    def execute(self, node):
        """
        :type node: srbc.tgbot.models.TGBotNode
        """
        node.set_next_node(self.node_key)


class TimeoutRedirect(TGBotAction):
    def execute(self, node):
        self.need_to_abort = False
        
        prev_node_data = node.get_prev_node_data()
        if prev_node_data['time']:
            now = round(datetime.now().timestamp())
            diff = now-prev_node_data['time']

            if diff > settings.DJANGO_TELEGRAMBOT_QUESTION_TIMEOUT:
                node.set_next_node(NodeNames.BACK_TO_MAIN_MENU_BY_TIMEOUT)
                self.need_to_abort = True


class GoToChosenNode(TGBotAction):
    """
    Переход в ноду, которую выбрал пользователь (по нажатию на клавиатуре).
    """

    def execute(self, node):
        """
        :type node: srbc.tgbot.models.TGBotNode
        """
        chosen_node_key = node.shared_results['validators'].get('ChooseNode')
        if chosen_node_key:
            node.set_next_node(node_key=chosen_node_key)


class GoToRouterNode(TGBotAction):
    """
    Переход из данной ноды с именем X в ноду с именем X_ROUTER.
    """

    def execute(self, node):
        """
        :type node: srbc.tgbot.models.TGBotNode
        """
        router_node_key = '%s_ROUTER' % node.node_key
        node.set_next_node(router_node_key)


class GoToChosenNodeOrGoToNode(GoToNode):
    """
    Если пользователь нажал на клавиатуре кнопку (выбрал ноду), то переход в эту ноду.
    Иначе (если не нажимал на кнопку на клавиатуре) - переход в заданную нодую
    """

    def execute(self, node):
        """
        :type node: srbc.tgbot.models.TGBotNode
        """
        chosen_node_key = node.shared_results['validators'].get('ChooseNode')
        if chosen_node_key:
            node.set_next_node(node_key=chosen_node_key)
        else:
            super(GoToChosenNodeOrGoToNode, self).execute(node=node)


class GoToNodeByTernaryOperator(TGBotAction):
    """
    Переход в ноду определяется тернарном оператором.
    """
    ternary_function = None
    node_key_true = None
    node_key_false = None

    def __init__(self, ternary_function, node_key_true, node_key_false):
        super(GoToNodeByTernaryOperator, self).__init__()
        self.ternary_function = ternary_function
        self.node_key_true = node_key_true
        self.node_key_false = node_key_false

    def execute(self, node):
        if self.ternary_function():
            node.set_next_node(self.node_key_true)
        else:
            node.set_next_node(self.node_key_false)

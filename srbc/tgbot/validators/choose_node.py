# -*- coding: utf-8 -*-
from srbc.tgbot.actions import SendMessage
from srbc.tgbot.config import NodeTranslations
from srbc.tgbot.models import TGBotValidator
from srbc.tgbot.utils import translate as _

__all__ = ('ChooseNode', 'ChooseNodeOrGoNextNode')


class ChooseNode(TGBotValidator):
    """
    Валидирует входящее сообщение от пользователя.
    Если пользователь нажал на кнопку на клавиатуре,
    то по пришедшему тексту (кнопки) валидатор определит какой ноде соответствует это нажатие.
    """

    def is_valid(self, node):
        prev_node_data = node.get_prev_node_data()
        keyboard_dict = {item.text: item.node_key for row in prev_node_data['keyboard'] for item in row}
        chosen_node_key = keyboard_dict.get(node.update.message.text)
        if chosen_node_key:
            node.shared_results['validators'][ChooseNode.__name__] = chosen_node_key
            return True

        self._failure_actions = [
            SendMessage(messages=[_(NodeTranslations.CHOOSE_CORRECT_NODE__TXT)], keyboard=prev_node_data['keyboard'])
        ]
        return False


class ChooseNodeOrGoNextNode(ChooseNode):
    """
    Делает тоже самое что и ChooseNode, но, если не нашло сопоставления, не выдает ошибку.
    """

    def is_valid(self, node):
        prev_node_data = node.get_prev_node_data()
        keyboard_dict = {item.text: item.node_key for row in prev_node_data['keyboard'] for item in row}
        chosen_node_key = keyboard_dict.get(node.update.message.text)
        if chosen_node_key:
            node.shared_results['validators'][ChooseNode.__name__] = chosen_node_key

        return True

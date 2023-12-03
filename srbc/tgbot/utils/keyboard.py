# -*- coding: utf-8 -*-
from srbc.tgbot.config import NodeNames
from .translator import translate

__all__ = ('TGRouterButton', 'keyboard_to_text')


class TGRouterButton(object):
    """
    Класс служит для того, чтобы хранить в одном объекте данные, необходимые для:
    1) вывода ТГ-сообщения с текстом в клавиатуре
    2) хранения выведенной клавиатуре в редисе
    3) клавитура в свою очередь - это набор рарзешенных пользователю переходов в ноды
    """
    __slots__ = ['node_key', 'text']

    def __init__(self, node_key, text=None, auto_translation=True):
        node_key = getattr(NodeNames, node_key, None)
        if not node_key:
            raise ValueError('Wrong key [%s]' % node_key)

        self.node_key = node_key

        if text:
            self.text = text
        elif auto_translation:
            self.text = translate(key=self.node_key)
        else:
            raise ValueError('Translation not found')

    def __repr__(self):
        return self.node_key


def keyboard_to_text(keyboard_data):
    """
    Преобразует данные вида [[TGRouterButton, TGRouterButton], [TGRouterButton]] в [[text, text], [text]]
    """
    if not isinstance(keyboard_data, list):
        return keyboard_data

    text_keyboard = []
    for row in keyboard_data:
        _row = []
        for item in row:
            if isinstance(item, TGRouterButton):
                _row.append(item.text)
            else:
                _row.append(item)
        text_keyboard.append(_row)

    return text_keyboard

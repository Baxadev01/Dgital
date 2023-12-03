# -*- coding: utf-8 -*-

from copy import deepcopy
from rest_framework.exceptions import ErrorDetail


def simplify_errors(ed, fd, rd=None):
    """ Рекурсивно проходится по ошибкам drf-сериализаторы и формирует упрощенный список ошибок.

    Например, для таких ошибок, полученных от drf-валидатора
    {'wake_up_time': [u'Неправильный формат времени. Используйте один из этих форматов: hh:mm[:ss[.uuuuuu]].'],
     'meals_data': [
        {'components': [
            {'external_link': [u'Введите корректный URL.'],
             'weight': [u'Требуется численное значение.']}
             ]
         }]
     }

     Сформирует упрощенный список ошибок
     [  u'Время пробуждения: Неправильный формат времени. Используйте один из этих форматов: hh:mm[:ss[.uuuuuu]].',
        u'Ссылка на описание продукта: Введите корректный URL.',
        u'Вес или эквивалент: Требуется численное значение.']

    :param ed: error data - данные об ошибках
    :type ed: list | dict | ErrorDetail
    :param fd: fields data  - данные поля с ошибкой
    :type fd: rest_framework.utils.serializer_helpers.BindingDict | django.db.models.fields.Field
    :param rd: список упрощенных ошибок
    :type rd: list
    :return: list
    """
    rd = [] if rd is None else rd

    fd = deepcopy(fd)
    ed = deepcopy(ed)

    if isinstance(ed, dict):
        for field_name, error_data in list(ed.items()):
            _fd = fd[field_name] if fd.get(field_name) else field_name
            if hasattr(_fd, 'child'):
                _fd = _fd.child.fields

            simplify_errors(error_data, _fd, rd)

        return rd

    elif isinstance(ed, list):
        for error_data in ed:
            simplify_errors(error_data, fd, rd)

        return rd

    elif isinstance(ed, ErrorDetail):
        if hasattr(fd, 'label'):
            label = fd.label
        elif hasattr(fd, 'serializer'):
            label = fd.serializer.label
        else:
            label = fd
        rd.append('%s: %s' % (label, ed))
        return rd

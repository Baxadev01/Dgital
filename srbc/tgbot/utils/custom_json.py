# -*- coding: utf-8 -*-

import json
from json import JSONDecoder, JSONEncoder
from .keyboard import TGRouterButton

__all__ = ('json_dumps', 'json_loads')


class CustomEncoder(JSONEncoder):
    """
    Специальным(удобным) образом храним TGRouterButton - данные в json.
    """
    def default(self, obj):
        if isinstance(obj, TGRouterButton):
            return {
                '_type': 'TGRouterButton',
                'node_key': str(obj.node_key),
                'text': obj.text
            }


class CustomDecoder(JSONDecoder):
    """
    Если в json есть наша сущность TGRouterButton, то после декодирования в данных будет объект TGRouterButton.
    """
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        if '_type' not in obj:
            return obj
        if obj['_type'] == 'TGRouterButton':
            return TGRouterButton(node_key=obj['node_key'], text=obj['text'], )
        return obj


def json_dumps(data):
    return json.dumps(data, cls=CustomEncoder)


def json_loads(data):
    return json.loads(data, cls=CustomDecoder)

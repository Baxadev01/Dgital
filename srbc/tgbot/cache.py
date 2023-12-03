from datetime import datetime
import redis

from srbc.tgbot.utils import json_loads, json_dumps

REDIS_CACHE = redis.Redis()

REDIS_KEY = 'TG_BOT_PREV_NODE_DATA'


def save_user_current_data(user_id, node_key, keyboard_data, partial_messages):
    now = datetime.now()
    prev_node_data = {
        'node_key': node_key,
        'keyboard': keyboard_data,
        'partial_messages': partial_messages,
        'time': round(now.timestamp())
    }
    REDIS_CACHE.hset(REDIS_KEY, str(user_id), json_dumps(prev_node_data))


def get_user_current_data(user_id):
    json_data = REDIS_CACHE.hget(REDIS_KEY, str(user_id))
    json_data = json_loads(json_data) if json_data else {}
    prev_node_data = {
        'node_key': json_data.get('node_key'),
        'keyboard': json_data.get('keyboard'),
        'partial_messages': json_data.get('partial_messages'),
        'time': json_data.get('time', None),
    }
    return prev_node_data


def remove_user_current_data(user_id):
    REDIS_CACHE.hdel(REDIS_KEY, str(user_id))

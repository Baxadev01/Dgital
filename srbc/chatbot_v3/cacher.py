import redis
from aenum import Constant

class Tables(Constant):
    STATES = 'states'

cacher = redis.Redis()

def save_user_current_state(userId, state):
    cacher.hset(Tables.STATES, str(userId), str(state))
    return 

def get_user_current_state(userId):
    return cacher.hget(Tables.STATES, str(userId))
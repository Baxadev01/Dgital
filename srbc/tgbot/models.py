# -*- coding: utf-8 -*-

import abc
import logging

import six
# from typing import List, Dict, Text, Optional

__all__ = ('TGBotNode', 'TGBotAction', 'TGBotValidator',)

from django.db import ProgrammingError

logger = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class TGBotAction(object):

    # если true = то нужно прерывать цепочку дальнейших действий в хендлерах
    need_to_abort = False

    @abc.abstractmethod
    def execute(self, node):
        """

        :param node:
        :type node: srbc.tgbot.models.TGBotNode
        :return:
        """
        pass


@six.add_metaclass(abc.ABCMeta)
class TGBotValidator(object):
    _failure_actions = list()  # type: List
    node = None

    @abc.abstractmethod
    def is_valid(self, node):
        """
        Checks if is node valid. Builds Failure Actions list if not.


        :type node: TGBotNode
        :rtype: bool
        """
        self.node = node

        return True

    def get_failure_actions(self):
        """
        :rtype: List of TGBotAction
        """
        return self._failure_actions


@six.add_metaclass(abc.ABCMeta)
class TGBotNode(object):
    node_key = None  # type: Text
    validators = []  # type: List[TGBotValidator]
    handlers = []  # type: List[TGBotAction]

    # process node after previous one is processed
    auto_processing = False  # type: bool

    bot = None  # type: Optional['telegram.bot.Bot']
    update = None  # type: Optional['telegram.update.Update']
    _user = None  # type: Optional['django.contrib.auth.models.User']
    _tg_user_id = None  # type: Optional[int]

    _next_node_key = None  # type: Optional[basestring]

    def __init__(self, bot, update, user=None, tg_user_id=None, prev_node_data=None):
        self.bot = bot
        self.update = update
        if user:
            self._user = user
            if self._user.profile.telegram_id:
                self._tg_user_id = self._user.profile.telegram_id
        elif tg_user_id:
            self._tg_user_id = tg_user_id
        self._prev_node_data = prev_node_data  # Optional[typing.Mapping]
        # validated data from self.validators
        self.partial_messages = []  # type: List[str]
        # данные для обмена между валидаторами и хендлерами
        self.shared_results = {'validators': {}, 'handlers': {}}  # type: Dict

    @abc.abstractmethod
    def get_messages(self):
        """
        :rtype: Optional[List[Text]]
        """
        return None

    @abc.abstractmethod
    def get_keyboard(self):
        """
        :rtype: Optional[List[List[Text]]]
        """
        return None

    def get_user(self):
        return self._user

    def get_tg_user_id(self):
        return self._tg_user_id

    def get_prev_node_data(self):
        _prev_node_data = self._prev_node_data or {}
        return {
            'node_key': _prev_node_data.get('node_key'),
            'keyboard': _prev_node_data.get('keyboard'),
            'partial_messages': _prev_node_data.get('partial_messages'),
            'time': _prev_node_data.get('time', None)
        }

    def process_request(self):
        for validator in self.validators:
            if not issubclass(validator.__class__, TGBotValidator):
                raise ProgrammingError("Invalid validator %s in TGBotNode <%s>" % (
                    validator.__class__.__name__, self.__class__.__name__
                ))

            # Get actions in case of validation not passed
            if not validator.is_valid(node=self):
                failure_actions = validator.get_failure_actions()

                if failure_actions:
                    for action in failure_actions:
                        action.execute(node=self)

                    return self._next_node_key

        if not self.handlers:
            raise ProgrammingError("Empty handlers in TGBotNode <%s>" % self.__class__.__name__)

        for handler in self.handlers:
            if not issubclass(handler.__class__, TGBotAction):
                raise ProgrammingError(
                    "Invalid handler %s in TGBotNode <%s>" % (
                        handler.__class__.__name__, self.__class__.__name__
                    )
                )

            handler.execute(node=self)
            if handler.need_to_abort:
                break

        return self._next_node_key

    def set_next_node(self, node_key):
        """
        :type node_key: basestring
        """
        self._next_node_key = node_key


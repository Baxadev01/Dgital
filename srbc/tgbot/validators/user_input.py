import emoji

from srbc.tgbot.actions import SendMessage
from srbc.tgbot.config import NodeTranslations
from srbc.tgbot.models import TGBotValidator
from srbc.tgbot.utils import translate as _

__all__ = ('TextInput', )


class TextInput(TGBotValidator):

    def __init__(self, min_length=20, max_length=None, allow_emoji=False):
        self.min_length = min_length
        self.max_length = max_length
        self.allow_emoji = allow_emoji

    def is_valid(self, node):
        message = node.update.message
        error_messages = []
        if node.update.message:
            self._validate_min_max_length(message, error_messages)
            self._validate_emoji(message, error_messages)
            self._validate_hashtag(message, error_messages)
            if error_messages:
                prev_node_data = node.get_prev_node_data()
                self._failure_actions = [SendMessage(messages=error_messages, keyboard=prev_node_data['keyboard'])]
                return False
            else:
                return True
        else:
            self._failure_actions = [
                SendMessage(
                    messages=[_(NodeTranslations.TEXT_INPUT_VALIDATION_FAILED__TXT)], keyboard=node.get_keyboard
                )
            ]
            return False

    def _validate_min_max_length(self, message, error_messages):
        message = message.text
        if self.min_length and (len(message) < self.min_length):
            error_messages.append(_(NodeTranslations.TEXT_INPUT_MIN_MAX_VALIDATION_FAILED__TXT))
            return

        if self.max_length and (len(message)) > self.max_length:
            error_messages.append(_(NodeTranslations.TEXT_INPUT_MIN_MAX_VALIDATION_FAILED__TXT))
            return

    def _validate_emoji(self, message, error_messages):
        message = message.text
        if self.allow_emoji:
            return

        if any(c in emoji.UNICODE_EMOJI for c in message):
            error_messages.append(_(NodeTranslations.TEXT_INPUT_EMOJI_NOT_ALLOWED__TXT))

    def _validate_hashtag(self, message, error_messages):
        if any(e.type == 'hashtag' for e in message.entities):
            error_messages.append(_(NodeTranslations.TEXT_INPUT_HASHTAG_NOT_ALLOWED__TXT))

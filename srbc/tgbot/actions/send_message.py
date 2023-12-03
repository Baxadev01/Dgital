from django.conf import settings
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

from content.utils import store_dialogue_reply
from srbc.tgbot.models import TGBotAction
from srbc.tgbot.utils import keyboard_to_text

__all__ = ('SendMessage', 'DefaultSendMessages', 'SendMessageToStuff')


class SendMessage(TGBotAction):
    PARSE_MODE_MARKDOWN = 'Markdown'
    PARSE_MODE_HTML = 'HTML'
    PARSE_MODE_NONE = None

    message = None
    keyboard = None
    parse_mode = None

    def __init__(self, messages, keyboard=None, parse_mode=PARSE_MODE_MARKDOWN):
        super(SendMessage, self).__init__()
        self.messages = messages
        self.keyboard = keyboard
        self.parse_mode = parse_mode

    def execute(self, node):
        if callable(self.messages):
            messages = self.messages()
        else:
            messages = self.messages

        keyboard = None

        if self.keyboard:
            if callable(self.keyboard):
                keyboard = self.keyboard()
            else:
                keyboard = self.keyboard

        if keyboard:
            keyboard = keyboard_to_text(keyboard)

        for message in messages:
            msg = node.bot.send_message(
                chat_id=node.get_tg_user_id(),
                text=message,
                reply_markup=ReplyKeyboardMarkup(keyboard=keyboard) if keyboard else ReplyKeyboardRemove(),
                parse_mode=self.parse_mode,
                disable_web_page_preview=True
            )

            store_dialogue_reply(
                user=node.get_user(), message=message, message_id=msg.message_id,
                tg_user_id=node.get_tg_user_id()
            )


class DefaultSendMessages(TGBotAction):
    def execute(self, node):
        SendMessage(messages=node.get_messages, keyboard=node.get_keyboard).execute(node=node)


class SendMessageToStuff(TGBotAction):

    def __init__(self, get_text_handler):
        self.get_text_handler = get_text_handler

    def execute(self, node):
        staff_notification_message = self.get_text_handler()
        node.bot.send_message(
            chat_id=settings.CHATBOT_NOTIFICATION_GROUP_ID,
            text=staff_notification_message,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

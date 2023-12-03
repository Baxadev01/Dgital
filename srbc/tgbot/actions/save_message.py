# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils import timezone

from content.models import TGMessage
from srbc.models import UserNote
from srbc.tgbot.models import TGBotAction

__all__ = ('SaveTGMessage', 'PreSaveMessage', 'SaveUserNote')


class SaveTGMessage(TGBotAction):
    TYPE_QUESTION = TGMessage.TYPE_QUESTION
    TYPE_FORMULA = TGMessage.TYPE_FORMULA
    TYPE_MEAL = TGMessage.TYPE_MEAL
    TYPE_FEEDBACK = TGMessage.TYPE_FEEDBACK

    def __init__(self, message_type):
        """
        :type message_type: basestring
        """
        super(SaveTGMessage, self).__init__()
        self.message_type = message_type

    def execute(self, node):
        """
        :type node: srbc.tgbot.models.TGBotNode
        """
        prev_node_data = node.get_prev_node_data()
        messages = prev_node_data.get('partial_messages', [])
        messages.append(node.update.message.text)
        text = '\n'.join(messages)
        q = TGMessage(
            author=node.get_user(),
            text=text,
            created_at=timezone.now(),
            message_type=self.message_type,
            tg_message_id=node.update.message.message_id
        )
        q.save()


class SaveUserNote(TGBotAction):
    TYPE_DOC = 'DOC'

    def __init__(self, message_type, get_text_handler):
        """
        :type message_type: basestring
        :type get_text_handler: callable
        """
        super(SaveUserNote, self).__init__()
        self.message_type = message_type
        self.get_text_handler = get_text_handler

    def execute(self, node):
        """
        :type node: srbc.tgbot.models.TGBotNode
        """
        text_to_save = self.get_text_handler()
        # text_to_save = node.update.message.text.replace("\n", "  \n")
        user_note = UserNote(
            user=node.get_user(),
            date_added=timezone.now(),
            label=self.message_type,
            is_published=False,
            # content=u"*Сообщение участника*:  \n%s" % text_to_save,
            content=text_to_save,
            author_id=settings.SYSTEM_USER_ID,
        )
        user_note.save()
        node.shared_results['handlers'][SaveUserNote.__name__] = user_note.pk


class PreSaveMessage(TGBotAction):
    """
    Сохраняет сообщение не в БД! Следующие ноды должны обработать сообщение и сохранить его.
    """

    def __init__(self, message_type='Рацион'):
        """
        :type message_type: basestring
        """
        super(PreSaveMessage, self).__init__()
        self.message_type = message_type

    def execute(self, node):
        """
        :type node: srbc.tgbot.models.TGBotNode
        """
        msg = '%s:\n%s\n' % (self.message_type, node.update.message.text)
        node.partial_messages.append(msg)

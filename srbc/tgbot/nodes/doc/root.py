# -*- coding: utf-8 -*-

from srbc.tgbot.actions import GoToNode, DefaultSendMessages, SaveUserNote, SendMessageToStuff, GoToChosenNodeOrGoToNode
from srbc.tgbot.bot import bot_manager
from srbc.tgbot.config import NodeNames, NodeTranslations
from srbc.tgbot.nodes.base import BaseNode, RouterNode, BaseEndNode
from srbc.tgbot.utils import TGRouterButton as TGRB, translate as _
from srbc.tgbot.validators import TextInput, ChooseNodeOrGoNextNode, WorkDay

__all__ = ('DocNode', 'DocRouterNode', 'DocInputNode')


@bot_manager.register(key=NodeNames.DOC)
class DocNode(BaseNode):
    validators = [WorkDay()]

    def get_messages(self):
        return [_(NodeTranslations.DOC__TXT)]

    def get_keyboard(self):
        return [
            [TGRB(NodeNames.BACK_TO_MAIN_MENU)],
        ]


@bot_manager.register(key=NodeNames.DOC_ROUTER)
class DocRouterNode(RouterNode):
    validators = [ChooseNodeOrGoNextNode()]
    handlers = [GoToChosenNodeOrGoToNode(node_key=NodeNames.DOC_INPUT)]


@bot_manager.register(key=NodeNames.DOC_INPUT)
class DocInputNode(BaseEndNode):

    def __init__(self, bot, update, user=None, tg_user_id=None, prev_node_data=None):
        super(DocInputNode, self).__init__(bot, update, user, tg_user_id, prev_node_data)
        self.validators = [TextInput()]
        self.handlers = [
            SaveUserNote(message_type=SaveUserNote.TYPE_DOC, get_text_handler=self._get_text_for_user_note),
            SendMessageToStuff(get_text_handler=self._get_text_for_stuff_notification),
            DefaultSendMessages(),
            GoToNode(node_key=NodeNames.MAIN_MENU_ROUTER)
        ]

    def get_messages(self):
        return [_(NodeTranslations.DOC__SAVE_OK)]

    def _get_text_for_user_note(self):
        text_to_save = self.update.message.text.replace("\n", "  \n")
        text_to_save = "*Сообщение участника*:  \n%s" % text_to_save
        return text_to_save

    def _get_text_for_stuff_notification(self):
        user_note_pk = self.shared_results['handlers'][SaveUserNote.__name__]

        user = self.get_user()
        tag = "#обследование"
        staff_notification_message = "Участник [{username}](https://lk.selfreboot.camp/profile/!{user_pk}/) оставил " \
                                     "[уведомление](https://lk.selfreboot.camp/admin/srbc/usernote/{note_pk}/) " \
                                     "({tag}/*{label}*): \n```\n{note_text}```".format(
            username=user.username, user_pk=user.pk, note_pk=user_note_pk,
            tag=tag, label=SaveUserNote.TYPE_DOC,
            note_text=self.update.message.text
        )

        return staff_notification_message

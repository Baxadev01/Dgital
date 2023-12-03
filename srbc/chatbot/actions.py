# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils import timezone
from telegram.utils.helpers import escape_markdown

from content.models import TGMessage
from content.utils import store_dialogue_reply
from crm.models import RenewalRequest
from crm.utils.renewal import is_renewal_possible
from helpers import AttrDict
from srbc.chatbot.messages import bot_messages
from srbc.models import UserNote


class ChatbotMessageAction(object):
    bot = None
    update = None
    message = None
    user = None
    tag = None
    params = AttrDict()

    def __init__(self, bot, update, user, tag, **kwargs):
        self.bot = bot
        self.update = update
        self.message = update.message
        self.user = user
        self.tag = tag
        self.params = AttrDict(**kwargs)

        self.run()

    def run(self):
        raise NotImplemented


class ChatbotActionRenewal(ChatbotMessageAction):
    def run(self):
        renewal_possible, rejection_reason = is_renewal_possible(self.user)

        if isinstance(renewal_possible, RenewalRequest):
            renewal_possible.comment += "\n%s  \n[%s] %s" % (
                "*" * 20,
                timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.message.text,
            )
            renewal_possible.status = 'NEW'
            renewal_possible.save(update_fields=['status', 'comment'])

            if renewal_possible.usernote:
                renewal_possible.usernote.content = "Запрос на продолжение:  \n%s" % \
                                                    renewal_possible.comment.replace("#", "\#")
                renewal_possible.usernote.save()
            else:
                renewal_note = UserNote(
                    user=self.user,
                    date_added=timezone.now(),
                    label='NB',
                    is_published=False,
                    content="Запрос на продолжение:  \n%s" % renewal_possible.comment.replace("#", "\#"),
                    author_id=settings.SYSTEM_USER_ID
                )
                renewal_note.save()
                renewal_possible.usernote = renewal_note
                renewal_possible.save(update_fields=['usernote'])

            msg = self.bot.send_message(
                chat_id=self.message.chat_id,
                text="Заявка обновлена и дополнена. Спасибо."
            )

            store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

        renewal_note = UserNote(
            user=self.user,
            date_added=timezone.now(),
            label='NB',
            is_published=False,
            content="Запрос на продолжение:  \n%s" % self.message.text.replace("#", "\#"),
            author_id=settings.SYSTEM_USER_ID
        )
        renewal_note.save()

        new_request = RenewalRequest(
            user=self.user,
            comment=self.message.text,
            request_type=self.params.flag,
            usernote=renewal_note
        )
        new_request.save()
        if self.params.flag == 'POSITIVE':
            msg = self.bot.send_message(
                chat_id=self.message.chat_id,
                text="Ваша заявка принята и записана. О результатах её рассмотрения я сообщу."
            )
        else:
            msg = self.bot.send_message(
                chat_id=self.message.chat_id,
                text="Ваша заявка принята. Благодарим за сотрудничество. "
                     "Не забывайте предоставлять данные до конца участия."
            )

        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)


class ChatbotActionReply(ChatbotMessageAction):
    default_message = "Уведомление принято. Спасибо."

    def run(self):
        if self.params.message:
            response_message = self.params.message
        else:
            response_message = self.default_message
        msg = self.bot.send_message(
            chat_id=self.message.chat_id,
            text=response_message
        )

        store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)


class ChatbotActionSaveNote(ChatbotMessageAction):
    def run(self):
        text_to_save = self.message.text.replace("#", "\#")
        text_to_save = text_to_save.replace("\n", "  \n")
        new_note = UserNote(
            user=self.user,
            date_added=timezone.now(),
            label=self.params.label,
            is_published=False,
            content="*Сообщение участника*:  \n%s" % text_to_save,
            author_id=settings.SYSTEM_USER_ID,
        )

        new_note.save()

        # msg = self.bot.send_message(
        #     chat_id=self.message.chat_id,
        #     text=u"Уведомление принято. Спасибо."
        # )
        #
        # store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)

        if self.params.get('raise_alarm', False):
            staff_notification_message = "Участник [%s](https://lk.selfreboot.camp/profile/!%s/) оставил " \
                                         "[уведомление](https://lk.selfreboot.camp/admin/srbc/usernote/%s/) " \
                                         "(%s/*%s*): \n```\n%s```" % (
                                             self.user.username,
                                             self.user.pk,
                                             new_note.pk,
                                             escape_markdown(self.tag.get('tag')),
                                             escape_markdown(new_note.label),
                                             self.message.text,
                                         )

            self.bot.send_message(
                chat_id=settings.CHATBOT_NOTIFICATION_GROUP_ID,
                text=staff_notification_message,
                parse_mode='Markdown',
                disable_web_page_preview=True
            )


class ChatbotActionQueueManual(ChatbotMessageAction):
    def run(self):
        q = TGMessage(
            author=self.user,
            text=self.message.text,
            created_at=timezone.localtime(timezone=timezone.utc),
            message_type=self.params.folder,
            tg_message_id=self.message.message_id
        )
        q.save()
        # msg = None
        # if self.params.folder == 'QUESTION':
        #     msg = self.bot.send_message(
        #         chat_id=self.message.chat_id,
        #         text=bot_messages.message_recorded_response_pending
        #     )
        # elif self.params.folder == 'FORMULA':
        #     msg = self.bot.send_message(
        #         chat_id=self.message.chat_id,
        #         text=bot_messages.message_recorded_response_pending
        #     )
        # elif self.params.folder == 'FEEDBACK':
        #     msg = self.bot.send_message(
        #         chat_id=self.message.chat_id,
        #         text=bot_messages.message_recorded
        #     )
        #
        # if msg:
        #     store_dialogue_reply(message=msg.text, message_id=msg.message_id, tg_user_id=msg.chat_id)


class ChatbotActionBlogRecord(ChatbotMessageAction):
    def run(self):
        pass


CHATBOT_ACTIONS = {
    "renewal": ChatbotActionRenewal,
    "note": ChatbotActionSaveNote,
    "manual": ChatbotActionQueueManual,
    "blog": ChatbotActionBlogRecord,
    "reply": ChatbotActionReply,
}

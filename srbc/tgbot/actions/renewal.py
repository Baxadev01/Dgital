# -*- coding: utf-8 -*-

from django.conf import settings
from django.utils import timezone

from crm.models import RenewalRequest
from crm.utils.renewal import is_renewal_possible
from srbc.models import UserNote
from srbc.tgbot.models import TGBotAction

__all__ = ('ProcessRenewalRequest', )


class ProcessRenewalRequest(TGBotAction):

    def __init__(self, stop_renewal=False):
        self.stop_renewal = stop_renewal

    def execute(self, node):
        """
        :type node: srbc.tgbot.models.TGBotNode
        """
        user = node.get_user()
        renewal_possible, _ = is_renewal_possible(user)

        if isinstance(renewal_possible, RenewalRequest):
            renewal_possible.comment += "\n%s  \n[%s] %s" % (
                "*" * 20,
                timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                node.update.message.text,
            )
            renewal_possible.status = 'NEW'
            renewal_possible.save(update_fields=['status', 'comment'])

            if renewal_possible.usernote:
                renewal_possible.usernote.content = "Запрос на продолжение:  \n%s" % \
                                                    renewal_possible.comment.replace("#", "\#")
                renewal_possible.usernote.save()
            else:
                renewal_note = UserNote(
                    user=user,
                    date_added=timezone.now(),
                    label='NB',
                    is_published=False,
                    content="Запрос на продолжение:  \n%s" % renewal_possible.comment.replace("#", "\#"),
                    author_id=settings.SYSTEM_USER_ID
                )
                renewal_note.save()
                renewal_possible.usernote = renewal_note
                renewal_possible.save(update_fields=['usernote'])

            return

        renewal_note = UserNote(
            user=user,
            date_added=timezone.now(),
            label='NB',
            is_published=False,
            content="Запрос на продолжение:  \n%s" % node.update.message.text.replace("#", "\#"),
            author_id=settings.SYSTEM_USER_ID
        )
        renewal_note.save()

        request_type = 'NEGATIVE' if self.stop_renewal else 'POSITIVE'
        new_request = RenewalRequest(
            user=user,
            comment=node.update.message.text,
            request_type=request_type,
            usernote=renewal_note
        )
        new_request.save()

import logging

from django.conf import settings
from django_telegrambot.apps import DjangoTelegramBot
from telegram.utils.helpers import escape_markdown

from content.models import TGNotification
from .base import IMailing

logger = logging.getLogger(__name__)


class SendMail(object):
    mailing_objects = []
    debug_info = []

    def register(self, mailing_cls):
        if not issubclass(mailing_cls, IMailing):
            return mailing_cls

        obj = mailing_cls()
        if obj.can_mail_now():
            self.mailing_objects.append(obj)
        return mailing_cls

    def collect(self, for_debug=False):
        report_template = '''
Рассылка `%(system_code)s` поставлена в очередь для отправки. 

Получателей: %(mails_count)d. 
Fingerprint: `%(fingerprint)s.`
'''

        for mail_obj in self.mailing_objects:
            if for_debug:
                print('fingerprint for "%s" is [%s]' % (mail_obj, mail_obj.fingerprint))

            mails_count = 0
            for user in mail_obj.get_users():

                if for_debug:
                    # do not create records in DB
                    self.debug_info.append("%s - %s" % (user.id, mail_obj.SYSTEM_CODE))
                else:
                    mails_count += 1
                    message = mail_obj.get_text_for_user(user)
                    TGNotification(
                        user_id=user.pk,
                        content=message,
                        fingerprint=mail_obj.fingerprint,
                        status='PENDING'
                    ).save()

            report = report_template % {
                'system_code': mail_obj.SYSTEM_CODE,
                'mails_count': mails_count,
                'fingerprint': mail_obj.fingerprint,
            }

            DjangoTelegramBot.dispatcher.bot.send_message(
                chat_id=settings.CHATBOT_NOTIFICATION_GROUP_ID,
                text=report,
                disable_web_page_preview=True,
                parse_mode='Markdown',
                timeout=1
            )

    def get_tg_mails_to_send(self):
        """
        :rtype: django.db.models.query.QuerySet
        """
        notes = TGNotification.objects.filter(status='PENDING')
        return notes


sender = SendMail()

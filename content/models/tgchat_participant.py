import logging

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

from django_telegrambot.apps import DjangoTelegramBot
from telegram.error import BadRequest, TimedOut

from .tgchat import TGChat

logger = logging.getLogger(__name__)

__all__ = ('TGChatParticipant',)


class TGChatParticipant(models.Model):
    STATUS_ALLOWED = 'ALLOWED'
    STATUS_JOINED = 'JOINED'
    STATUS_LEFT = 'LEFT'
    STATUS_RESTRICTED = 'RESTRICTED'
    STATUS_UNRESTRICTED = 'UNRESTRICTED'
    STATUS_BANNED = 'BANNED'

    STATUS_ITEM = (
        (STATUS_ALLOWED, _("Allowed")),
        (STATUS_JOINED, _("Joined")),
        (STATUS_LEFT, _("Left")),
        (STATUS_RESTRICTED, _("Restricted")),
        (STATUS_UNRESTRICTED, _("Unrestricted")),
        (STATUS_BANNED, _("Banned")),
    )

    user = models.ForeignKey(User, related_name='membership', on_delete=models.CASCADE)
    chat = models.ForeignKey(TGChat, related_name='membership', on_delete=models.CASCADE)

    status = models.CharField(
        blank=True,
        max_length=50,
        choices=STATUS_ITEM,
        default=STATUS_ALLOWED
    )
    status_changed = models.DateTimeField(auto_now=True)

    def __str__(self):
        return '%s [%s]' % (
            self.user.username, self.user.profile.wave.title if self.user.profile.wave else 'Не является участником'
        )

    class Meta:
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['user']),
            models.Index(fields=['chat']),
        ]

        verbose_name = _('участник чата')
        verbose_name_plural = _('участники чатов')


def manage_chat_user_status(sender, instance, **kwargs):
    if instance.user.profile.telegram_id:
        if instance.status == 'BANNED':
            try:
                DjangoTelegramBot.dispatcher.bot.kick_chat_member(
                    chat_id=instance.chat.tg_id,
                    user_id=instance.user.profile.telegram_id
                )
            except BadRequest as e:
                if e.message == 'User_not_participant':
                    pass
                else:
                    logger.info('Can\'t ban user %s in chat %s' % (instance.user, instance.chat,))
                    raise e
            except TimedOut as e:
                return manage_chat_user_status(sender, instance, **kwargs)

        if instance.status == 'RESTRICTED':
            try:
                DjangoTelegramBot.dispatcher.bot.restrict_chat_member(
                    chat_id=instance.chat.tg_id,
                    user_id=instance.user.profile.telegram_id,
                    can_add_web_page_previews=False,
                    can_send_media_messages=False,
                    can_send_messages=False,
                    can_send_other_messages=False
                )
            except BadRequest as e:
                if e.message == 'User_not_participant':
                    pass
                else:
                    raise e
            except TimedOut as e:
                return manage_chat_user_status(sender, instance, **kwargs)

        if instance.status == 'UNRESTRICTED' and instance.chat.chat_type == 'CHAT':
            try:
                DjangoTelegramBot.dispatcher.bot.restrict_chat_member(
                    chat_id=instance.chat.tg_id,
                    user_id=instance.user.profile.telegram_id,
                    can_add_web_page_previews=True,
                    can_send_media_messages=True,
                    can_send_messages=True,
                    can_send_other_messages=True
                )
            except BadRequest as e:
                if e.message == 'Bots can\'t add new chat members':
                    instance.status = 'ALLOWED'
                    instance.save()
                    return
                else:
                    raise e
            except TimedOut as e:
                return manage_chat_user_status(sender, instance, **kwargs)

            instance.status = 'JOINED'
            instance.save()
            return

        if instance.status == 'ALLOWED':
            try:
                DjangoTelegramBot.dispatcher.bot.unban_chat_member(
                    chat_id=instance.chat.tg_id,
                    user_id=instance.user.profile.telegram_id
                )
            except TimedOut as e:
                return manage_chat_user_status(sender, instance, **kwargs)


post_save.connect(manage_chat_user_status, sender=TGChatParticipant)

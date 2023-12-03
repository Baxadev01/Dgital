import string

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

from .tgchat import TGChat

__all__ = ('ChatQuestion',)


class ChatQuestion(models.Model):
    message_id = models.BigIntegerField()
    shortcut = models.CharField(max_length=6, blank=True, null=True)
    author = models.ForeignKey(User, related_name='chat_questions_by', null=True, on_delete=models.SET_NULL)
    chat = models.ForeignKey(TGChat, related_name='chat_questions', on_delete=models.CASCADE)
    question_time = models.DateTimeField()
    created_time = models.DateTimeField(auto_now_add=True)
    question_text = models.TextField(blank=True)
    category = models.CharField(
        max_length=50,
        choices=(
            ("GENERAL", "#вопрос"),
            ("IG", "#сменаника"),
            ("MEETING", "#вопросыкмитингу"),
            ("FEEDBACK", "#отзыв"),
            ("MEAL", "#рацион"),
            ("DOC", "#док"),
        ),
    )
    is_answered = models.BooleanField(blank=True, default=False)
    answer_text = models.TextField(blank=True)
    answered_time = models.DateTimeField(blank=True, null=True)
    answered_by = models.ForeignKey(
        User,
        related_name='chat_questions_replies_by',
        limit_choices_to={
            "is_staff": True,
        },
        blank=True,
        null=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['shortcut']),
            models.Index(fields=['is_answered']),
            models.Index(fields=['chat']),
            models.Index(fields=['message_id']),
        ]
        verbose_name = _('вопрос в чате')
        verbose_name_plural = _('вопросы в чатах')


def set_question_shortcut(sender, instance, **kwargs):
    def int2base(x, base):
        digs = string.digits + string.letters

        if x < 0:
            sign = -1
        elif x == 0:
            return digs[0]
        else:
            sign = 1

        x *= sign
        digits = []

        while x:
            digits.append(digs[x % base])
            x /= base

        if sign < 0:
            digits.append('-')

        digits.reverse()

        return ''.join(digits)

    if instance.shortcut is None:
        message_id = '%04d' % instance.pk
        last_id_symbols = message_id[-3:]
        extra_id_symbol = message_id[-4:-3]
        tail_int = int(last_id_symbols, 16) + 16 ** 3 * int(extra_id_symbol, 16) / 2
        prefixes = {
            "GENERAL": "s",
            "IG": "s",
            "MEETING": "m",
            "DOC": "d",
            "FEEDBACK": "f",
            "MEAL": "r",
        }

        prefix = prefixes.get(instance.category)

        instance.shortcut = '%s%s' % (prefix, int2base(tail_int, 36))
        instance.save(update_fields=['shortcut'])

    return


post_save.connect(set_question_shortcut, sender=ChatQuestion)

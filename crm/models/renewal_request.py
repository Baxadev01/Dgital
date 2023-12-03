from django.contrib.auth.models import User

from django.db import models
from django.utils.translation import ugettext_lazy as _

from srbc.models.user_note import UserNote

__all__ = ('RenewalRequest',)


class RenewalRequest(models.Model):
    request_type = models.CharField(
        max_length=10,
        choices=(
            ('POSITIVE', "#япродолжаю"),
            ('NEGATIVE', "#яНЕпродолжаю"),
        ),
        verbose_name="Хэштег"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField(verbose_name="Отзыв")
    comment_internal = models.TextField(verbose_name="Служебная заметка", blank=True, default='')
    date_added = models.DateTimeField(auto_now_add=True)
    payment_special = models.BooleanField(verbose_name="Особые условия оплаты", blank=True, default=False)
    status = models.CharField(
        max_length=25,
        blank=True,
        default='NEW',
        choices=(
            ('NEW', 'Новый'),
            ('PENDING', 'Ожидает ответа участника'),
            ('PREACCEPTED', 'Предварительно одобрен'),
            ('TBD', 'Требуется согласование'),
            ('REJECTED', 'Отклонен'),
            ('ACCEPTED', 'Одобрен'),
        )
    )
    usernote = models.ForeignKey(UserNote, blank=True, null=True, on_delete=models.SET_NULL)

    class Meta:
        verbose_name = 'запрос на продление'
        verbose_name_plural = 'запросы на продление'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['request_type']),
            models.Index(fields=['status']),
            models.Index(fields=['date_added']),
        ]

from django.contrib.auth.models import User

from django.db import models
from django.utils.translation import ugettext_lazy as _

__all__ = ('DiscountCode',)


class DiscountCode(models.Model):
    code = models.CharField(max_length=100, unique=True)
    expiring_at = models.DateTimeField(blank=True, null=True)
    is_applied = models.BooleanField(default=False, blank=True)
    applied_at = models.DateTimeField(blank=True, null=True)
    applied_by = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)

    # TODO: rename to discount_percent
    dicount_percent = models.DecimalField(max_digits=8, decimal_places=4)

    payment_type = models.CharField(
        max_length=20, blank=True, null=True,
        choices=(
            ('CLUB', _("Оплата участия в клубе")),
            ('CHANNEL', _("Оплата участия в проекте (заочный)")),
            ('CHAT', _("Оплата участия в проекте (очный)")),
        )
    )

    def __str__(self):
        return '%s (%0.2f%%)' % (self.code, self.dicount_percent)

    def __repr__(self):
        return '<%s (%s)>' % (self.__class__.__name__, self.code)

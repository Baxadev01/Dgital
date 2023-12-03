from datetime import datetime
from django.contrib.auth.models import User

from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from .discount_code import DiscountCode
from srbc.models.subscription import Subscription
from srbc.models.tariff import Tariff
from srbc.models.wave import Wave

__all__ = ('ApplePayment', 'GooglePayment', 'StripePayment', 'Payment', 'Order', 'YandexPayment')


class Order(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    payment_provider = models.CharField(
        max_length=100,
        choices=(
            ('YA', _(u"Яндекс-Касса (банковская карта)")),

            ('PP', _(u"PayPal")),
            ('MANUAL', _(u"Вручную")),
        ),
        default='YA',
        blank=True,
        null=True
    )
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(
        max_length=100,
        choices=(
            ('PENDING', _("Ожидает оплаты")),
            ('PROCESSING', _("В обработке")),
            ('APPROVED', _("Оплачен")),
            ('CANCELED', _("Отменен")),
        ),
        default='PENDING'
    )

    date_added = models.DateTimeField(default=datetime.now, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=8)
    currency = models.CharField(
        max_length=3,
        choices=(
            ('RUB', _("Рубли")),
            ('EUR', _("Евро")),
        ),
        default='RUB'
    )

    discount_code = models.ForeignKey(DiscountCode, blank=True, null=True, on_delete=models.SET_NULL)
    tariff = models.ForeignKey(Tariff, blank=True, null=True, on_delete=models.SET_NULL)

    payment_type = models.CharField(
        max_length=100,
        choices=(
            ('CLUB', _("Оплата участия в клубе")),
            ('CHANNEL', _("Оплата участия в проекте (заочный)")),
            ('CHAT', _("Оплата участия в проекте (очный)")),
        )
    )
    payment_url = models.TextField(blank=True, null=True)
    wave = models.ForeignKey(
        'srbc.Wave',
        blank=True, null=True, on_delete=models.SET_NULL,
        related_name='wave_to_join',
        verbose_name="Payment wave"
    )
    paid_until = models.DateField(blank=True, null=True)
    last_updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    @property
    def is_payable(self):
        if self.amount is None:
            return False

        if self.payment_id:
            return False

        if not self.payment_provider:
            return False

        if not self.currency:
            return False

        return True

    class Meta:
        managed = False

        indexes = [
            models.Index(fields=['payment_provider']),
            models.Index(fields=['payment_type']),
            models.Index(fields=['currency']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_id']),
        ]

        verbose_name = 'Счёт'
        verbose_name_plural = 'Счета'


# все данные классы оплаты - сделаны для подписок, простые разовые платежи не менялись 
# ДЛЯ подписки
class ApplePayment(models.Model):
    def __str__(self):
        return self.pk

# ДЛЯ подписки
class GooglePayment(models.Model):
    def __str__(self):
        return self.pk

# ДЛЯ подписки
class StripePayment(models.Model):
    invoice_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.pk

class ProdamusPayment(models.Model):
    invoice_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.pk


# ДЛЯ подписки
class YandexPayment(models.Model):
    invoice_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.pk


class Payment(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_PROCESSING = 'PROCESSING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_CANCELED = 'CANCELED'

    PAYMENT_TYPE_CLUB = 'CLUB'
    PAYMENT_TYPE_CHANNEL = 'CHANNEL'
    PAYMENT_TYPE_CHAT = 'CHAT'
    PAYMENT_TYPE_NON_WAVE = 'NON_WAVE'

    PAYMENT_TYPE_ITEM = (
        (PAYMENT_TYPE_CLUB, _("Оплата участия в клубе")),
        (PAYMENT_TYPE_CHANNEL, _("Оплата участия в проекте (заочный)")),
        (PAYMENT_TYPE_CHAT, _("Оплата участия в проекте (очный)")),
        (PAYMENT_TYPE_NON_WAVE, _("Оплата участия по подписке (доступ к митингам)")),
    )

    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    payment_provider = models.CharField(
        max_length=100,
        choices=(settings.CRM_MODEL_PAYMENT_PROVIDER),
        default='YA',
        blank=True,
        null=True
    )
    payment_id = models.CharField(max_length=100, blank=True, null=True)

    subscription = models.ForeignKey(Subscription, related_name='payments', null=True, on_delete=models.SET_NULL)
    apple_payment = models.ForeignKey(ApplePayment, null=True, on_delete=models.SET_NULL)
    google_payment = models.ForeignKey(GooglePayment, null=True, on_delete=models.SET_NULL)
    stripe_payment = models.ForeignKey(StripePayment, null=True, on_delete=models.SET_NULL)
    yandex_payment = models.ForeignKey(YandexPayment, null=True, on_delete=models.SET_NULL)
    prodamus_payment = models.ForeignKey(ProdamusPayment, null=True, on_delete=models.SET_NULL)

    status = models.CharField(
        max_length=100,
        choices=(
            (STATUS_PENDING, _("Ожидает оплаты")),
            (STATUS_PROCESSING, _("В обработке")),
            (STATUS_APPROVED, _("Оплачен")),
            (STATUS_CANCELED, _("Отменен")),
        ),
        default=STATUS_PENDING
    )

    date_added = models.DateTimeField(default=datetime.now, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=8)
    currency = models.CharField(
        max_length=3,
        choices=(
            ('RUB', _("Рубли")),
            ('EUR', _("Евро")),
        ),
        default='RUB'
    )

    discount_code = models.ForeignKey(DiscountCode, blank=True, null=True, on_delete=models.SET_NULL)
    tariff = models.ForeignKey(Tariff, blank=False, null=True, on_delete=models.SET_NULL)

    payment_type = models.CharField(
        max_length=100,
        choices=PAYMENT_TYPE_ITEM
    )
    payment_url = models.TextField(blank=True, null=True)
    wave = models.ForeignKey(
        Wave,
        blank=True, null=True, on_delete=models.SET_NULL,
        # TODO по поиску не нашло использование этого релейтеда, поэтмоу просто переименовал
        # может даже лучше совсем выпилить эту связь
        related_name='wave_to_join_archive',
        verbose_name="Payment wave"
    )
    last_updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    @property
    def is_payable(self):
        if self.amount is None:
            return False

        if self.payment_id:
            return False

        if not self.payment_provider:
            return False

        if not self.currency:
            return False

        return True

    class Meta:
        indexes = [
            models.Index(fields=['payment_provider']),
            models.Index(fields=['payment_type']),
            models.Index(fields=['currency']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_id']),
        ]

        verbose_name = 'Счёт'
        verbose_name_plural = 'Счета'

        permissions = (
            ('add_advanced_payment', 'Добавление счета в продвинутом режиме'),
        )

    def __str__(self):
        return '%s' % self.pk


def bind_order_to_account(sender, instance, created, *args, **kwargs):
    # Если создаем ордер, который сразу аппрувнут или отменен - не нужно делать привязку
    if created and instance.status not in [Payment.STATUS_APPROVED, Payment.STATUS_CANCELED]:
        instance.user.application.active_payment_order = instance
        instance.user.application.save(update_fields=['active_payment_order'])


def clear_active_payment_order(sender, instance, created, update_fields, **kwargs):
    # если обновили статус до отмененного или подтвержденного - сбрасываем активный ордер у пользователя
    if update_fields is None or 'status' in update_fields:
        if instance.status in [Payment.STATUS_APPROVED, Payment.STATUS_CANCELED]:
            instance.user.application.active_payment_order = None
            instance.user.application.save(update_fields=['active_payment_order'])


post_save.connect(clear_active_payment_order, sender=Payment)
post_save.connect(bind_order_to_account, sender=Payment)

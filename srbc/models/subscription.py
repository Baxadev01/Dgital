from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .tariff import Tariff

__all__ = ('StripeSubscription', 'Subscription', 'YandexSubscription')


class AppleSubscription(models.Model):
    # пока введу тайтл, есть уникальные имена у подписок, которые задаются в настройках, если будет не нужно или будет как айди - заменим
    title = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.pk


class GoogleSubscription(models.Model):
    # пока введу тайтл, есть уникальные имена у подписок, которые задаются в настройках, если будет не нужно или будет как айди - заменим
    title = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.pk


class StripeSubscription(models.Model):
    # сгенеренный нами уникальный ключ
    subscription_id = models.CharField(max_length=100, blank=True, null=True)

    # ключ для идентификации в системе страйпа (приходит от страйпа)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return '%s' % self.stripe_subscription_id
    
class ProdamusSubscription(models.Model):
    # сгенеренный нами уникальный ключ
    subscription_id = models.CharField(max_length=100, blank=True, null=True)

    # ключ для идентификации в системе страйпа (приходит от страйпа)
    prodamus_subscription_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return '%s' % self.prodamus_subscription_id

class YandexSubscription(models.Model):
    # сгенеренный нами уникальный ключ
    subscription_id = models.CharField(max_length=100, blank=True, null=True)

    # ключ для идентификации в системе страйпа (приходит от страйпа)
    yandex_payment_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return '%s' % self.subscription_id


class Subscription(models.Model):
    STATUS_NEW = 'NEW'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_CANCELED = 'CANCELED'
    STATUS_EXPIRED = 'EXPIRED'

    STATUSES = (
        (STATUS_NEW, _('Новая')),
        (STATUS_ACTIVE, _('Активна')),
        (STATUS_CANCELED, _('Отменена')),
        (STATUS_EXPIRED, _('Истекла')),
    )

    user = models.ForeignKey(User, related_name='subscriptions', on_delete=models.CASCADE)
    tariff = models.ForeignKey(Tariff, related_name='subscriptions', on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUSES
    )

    # мб тут хватит 1 к 1 как все определимся точно
    google_subscription = models.OneToOneField(
        GoogleSubscription, related_name='subscription', on_delete=models.CASCADE, blank=True, null=True)
    apple_subscription = models.OneToOneField(AppleSubscription, related_name='subscription',
                                              on_delete=models.CASCADE, blank=True, null=True)
    stripe_subscription = models.OneToOneField(
        StripeSubscription, related_name='subscription', on_delete=models.CASCADE, blank=True, null=True)

    yandex_subscription = models.OneToOneField(
        YandexSubscription, related_name='subscription', on_delete=models.CASCADE, blank=True, null=True)
    prodamus_subscription = models.OneToOneField(
        ProdamusSubscription, related_name='subscription', on_delete=models.CASCADE, blank=True, null=True)
    

    # TODO можно ввести проверку, что хотя бы / только одно поле заполнено, через clean ?

    # TODO не забыть ввести по необходимости после написания всей логики
    # class Meta:
    #     indexes = []

    @property
    def valid_until(self):
        last_history_record = self.tariff.tariff_history.filter(
            payment__subscription_id=self.pk).order_by("-valid_until").first()
        # last_history_record = self.tariff.tariff_history.filter(user_id=self.user_id).order_by("-valid_until").first()

        if last_history_record:
            return last_history_record.valid_until

        return None

    # чтобы не выносить константы наружу
    @property
    def is_canceled(self):
        return self.status == self.STATUS_CANCELED

    @property
    def can_be_upgraded_to(self):
        if self.status == self.STATUS_CANCELED:
            return None

        slugs = settings.SUBSCRIPTION_UPGRADE_ABILITY.get(self.tariff.slug, None)

        if not slugs:
            return None
        
        return Tariff.objects.filter(slug__in=slugs)


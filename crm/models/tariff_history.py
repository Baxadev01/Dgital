from datetime import date
from django.contrib.auth.models import User, Group

from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

from .payments import Payment
from srbc.models.tariff import Tariff
from srbc.models.wave import Wave

__all__ = ('TariffHistory',)


class TariffHistory(models.Model):
    is_active = models.BooleanField(blank=True, default=True)

    user = models.ForeignKey(User, related_name='tariff_history', on_delete=models.CASCADE)
    tariff = models.ForeignKey(Tariff, related_name='tariff_history', on_delete=models.PROTECT)
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, null=True, blank=True, related_name='tariff_history')
    valid_from = models.DateField(db_index=True)
    valid_until = models.DateField(db_index=True)

    wave = models.ForeignKey(
        Wave,
        blank=True, null=True, on_delete=models.SET_NULL,
        related_name='tariff_history',
    )

    created_at = models.DateTimeField(auto_now_add=True)


def activate_participant(sender, instance, created, raw, using, update_fields, **kwargs):
    """

    :param sender:
    :param update_fields:
    :param instance:
    :type instance: Profile
    :param kwargs:
    :return:
    """

    if update_fields is None or 'is_active' in update_fields:
        if instance.is_active:
            user = instance.user
            participant_group = Group.objects.filter(name='Participant').first()
            if not user.groups.filter(name='Participant').exists():
                if participant_group:
                    participant_group.user_set.add(user)


post_save.connect(activate_participant, sender=TariffHistory)

# при любой модификации записи будем смотреть, что поменялось.


def update_profile_th_records(sender, instance, created, raw, using, update_fields, **kwargs):
    """

    :param sender:
    :param update_fields:
    :param instance:
    :type instance: Profile
    :param kwargs:
    :return:
    """
    today = date.today()

    th_values = User.objects.filter(
        id=instance.user_id
    ).values(
        'profile__active_tariff_history_id', 
        'profile__next_tariff_history_id'
    ).first()

    if instance.is_active:
        # определяем должна ли запись встать на место активной или следующей записи
        # и если да, то надо ли менять
        if instance.valid_until >= today >= instance.valid_from and \
                th_values['profile__active_tariff_history_id'] != instance.pk:
            instance.user.profile.active_tariff_history = instance
            instance.user.profile.save(update_fields=['active_tariff_history'])

        elif instance.valid_from > today and \
                th_values['profile__next_tariff_history_id'] != instance.pk:
            instance.user.profile.next_tariff_history = instance
            instance.user.profile.save(update_fields=['next_tariff_history'])

    # проверяем не надо ли скинуть из профайла запись
    else:
        if th_values['profile__active_tariff_history_id'] == instance.pk:
            instance.user.profile.active_tariff_history = None
            instance.user.profile.save(update_fields=['active_tariff_history'])
        elif th_values['profile__next_tariff_history_id'] == instance.pk:
            instance.user.profile.next_tariff_history = None
            instance.user.profile.save(update_fields=['next_tariff_history'])


post_save.connect(update_profile_th_records, sender=TariffHistory)

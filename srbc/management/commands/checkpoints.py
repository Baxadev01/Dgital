# -*- coding: utf-8 -*-
import logging
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db.models.aggregates import Max

from srbc.models import User, Checkpoint
from srbc.utils.checkpoint_measurement import get_current_checkpoint_date, get_nearest_schedule_saturday

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """ (DEV-90) Обрабатывает чекпоинты:
    - если настала дата внесения очередного чекпоинта today = (D-3) - проходит по всем участникам,
    которые is_active = TRUE, is_in_club = False и создает чекпоинт
    - если прошло ровно три дня today = (D+3) - проходит по всем чекпоинтам,
    у которых is_editable = True  и выставлет is_editable = False
    """
    help = "Creates new checkpoints, deactivates old ones"

    def handle(self, *args, **options):
        # 1) получим ближайшую дату по расписанию - ее будем использовать для фильтра по юзерам
        today = date.today()
        sch_date = get_nearest_schedule_saturday(date=today)

        # 2) необходимые юзеры - is_active=True, is_in_club=False с датой начала потока меньшей sch_date
        users = User.objects.filter(
            tariff_history__is_active=True,
            tariff_history__valid_from__lte=today,
            tariff_history__valid_until__gte=today,
            tariff_history__tariff__tariff_group__is_wave=True,
            tariff_history__tariff__tariff_group__is_in_club=False,
            tariff_history__wave__start_date__lte=sch_date
        ).annotate(
            last_checkpoint=Max('checkpoints__date')
        ).select_related('profile')

        users_list = list(users.all())
        for user in users_list:
            # дата чекпоинта может быть разной в зависимости от даты старта потока
            # (в первую субботу после старта потока или в субботу по расписанию)
            checkpoint_date, is_editable = get_current_checkpoint_date(
                wave_start_date=user.profile.wave.start_date, tz=user.profile.timezone
            )
            delta_days = (checkpoint_date - today).days
            if is_editable:
                # user.last_checkpoint может быть None, если у юзера еще нет чекпоинтов
                condition = user.last_checkpoint is None or user.last_checkpoint < checkpoint_date
                if -3 < delta_days <= 3 and condition:
                    checkpoint = Checkpoint(user=user, date=checkpoint_date)
                    checkpoint.save()
                    logger.info('New checkpoint (id=%d) for user (id=%d)', checkpoint.id, user.id)
                elif delta_days <= -3:
                    logger.info('Make `is_editable=False` for checkpoints for user (id=%d)', user.id)
                    Checkpoint.objects.filter(user_id=user.id, is_editable=True).update(is_editable=False)

        # для остальных юзеров, которые не активны, обновляем is_editable
        Checkpoint.objects \
            .filter(is_editable=True) \
            .exclude(user__profile__is_active=True) \
            .update(is_editable=False)

        Checkpoint.objects \
            .filter(is_editable=True, date__lte=date.today() - timedelta(days=4)) \
            .update(is_editable=False)

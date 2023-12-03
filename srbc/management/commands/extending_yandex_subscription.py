# -*- coding: utf-8 -*-
import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from crm.utils.yandex_subscription import extending_subscription
from srbc.models import Subscription

from sentry_sdk import capture_event, capture_exception

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "проверяет подписки яндекса на продление"

    def handle(self, *args, **options):
        subs = Subscription.objects.filter(
            status=Subscription.STATUS_ACTIVE,
            yandex_subscription__isnull=False
        ).all()

        today = date.today()

        for sub in subs:
            try:
                active_th = sub.user.profile.active_tariff_history
                # Продлеваем, если:
                # 1. идет последний день активной подписки
                # 2. нет next_active_th (на всякий случай)
                if not active_th:
                    # что-то странное, кидаем ошибку и идем дальше
                    capture_exception(Exception('extending subscription %s. Active th not exist' % sub.pk))
                    continue

                if active_th.tariff != sub.tariff:
                    # тарифы не совпадают, может подписка оформлены во время волнового тарифа, ничего не делаем
                    continue

                if active_th.valid_until == today and not sub.user.profile.next_tariff_history:
                    # вызываем продление
                    extending_subscription(sub)

            except Exception as e:
                capture_exception(e)
                continue

        print('done')

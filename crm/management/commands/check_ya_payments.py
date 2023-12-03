# -*- coding: utf-8 -*-
import logging
from datetime import timedelta, datetime
from sentry_sdk import capture_exception

from django.core.management.base import BaseCommand
from django.utils import timezone

from crm.models import Payment
from crm.utils.payments import check_payment, confirm_order

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """ (DEV-99) Обрабатывает YA платежи.
    Если пользователь закрывает страницу оплаты, не вернувшись в ЛК,
    то ЛК не получает информации о том, что платеж прошел.
    Таким образом, данный скрипт проверяет и обрабатывает YA платежи:
        - все платежи старше 23 дней без payment_id - делает cancelled
        - все платежи старше 72 часов с payment_id - проверяет статус (если не оплачен - делает cancelled)
    """
    help = "Check YA payments and update there status"

    def handle(self, *args, **options):
        release_date = datetime.fromisoformat('2021-05-25T00:00:00+02:00')

        now = timezone.now()

        # 1) отменим все платежи старше 23 дней без payment_id
        days_ago = now - timedelta(days=23)
        orders_to_cancel = Payment.objects.filter(
            payment_id__isnull=True,
            payment_provider__in=['YA', 'YM'],
            date_added__lte=days_ago,
            status__in=['PENDING', 'PROCESSING'],
        ).select_related('user', 'user__application').all()

        for order in orders_to_cancel:
            order.status = 'CANCELED'
            order.save()

            logger.info(
                "Order #%s (PaymentId: %s) for user #%s (%s) was auto cancelled" % (
                    order.id,
                    order.payment_id,
                    order.user.id,
                    order.user.username,
                )
            )

            user_application = order.user.application
            if user_application.active_payment_order_id and user_application.active_payment_order_id == order.id:
                user_application.active_payment_order_id = None
                user_application.save(update_fields=['active_payment_order'])

        # 2) проверим все платежи старше 72 часов с payment_id
        hours_ago = now - timedelta(hours=72)
        orders_iterator = Payment.objects.filter(
            payment_id__isnull=False,
            payment_provider__in=['YA', 'YM'],
            status__in=['PENDING', 'PROCESSING'],
        ).iterator()

        for order in orders_iterator:
            # FIXME вот эту часть кажется, что тоже можно выпилить будет (видимо спустя время)
            old_status = order.status

            order = check_payment(order=order)

            if order.status == 'APPROVED':
                logger.info(
                    "Order #%s (%s) for user #%s (%s) was auto approved" % (
                        order.id,
                        order.user.id,
                        order.user.username,
                        old_status,
                    )
                )

                order = confirm_order(order)

                # TODO, пока для тестов основного алгоритма - можно оставить тут проверку
                if order.date_added > release_date:
                    # значит что-то странное и конфирм не пришел в нотификации
                    capture_exception(Exception('ya_check_command. Strange confirm %s', order.id))
                    continue

            if order.date_added <= hours_ago and order.status not in ['PROCESSING', 'APPROVED']:
                old_payment_id = order.payment_id
                # cancel_payment(order)
                logger.info(
                    "Order #%s (%s) for user #%s (%s) was cancelled for not paid after 72 hours after creation (%s)" % (
                        order.id,
                        old_payment_id,
                        order.user.id,
                        order.user.username,
                        old_status,
                    )
                )


import logging
from datetime import date, timedelta
from django.db.models import Q, Min

from content.tgmails.base import IMailing
from content.tgmails.sendmail import sender
from srbc.models import User, Wave

logger = logging.getLogger(__name__)

__all__ = ('Feedback',)


@sender.register
class Feedback(IMailing):
    SYSTEM_CODE = 'feedback'

    CRON_HOURS = 12
    CRON_MINUTES = 15

    def get_reference_date(self):
        # Периодичность: один раз в четыре недели, в понедельник через 3 дня после старта потока, в 12:15 МСК
        today = date.today()

        wave = Wave.objects.filter(
            start_date__lte=today
        ).order_by(
            '-start_date'
        ).first()

        if not wave:
            return None

        return wave.start_date + timedelta(days=3)

    def get_users(self):
        # старты первой хистори должен быть между 8 и 16 неделями
        today = date.today()
        start_date = today - timedelta(days=112)
        end_date = today - timedelta(days=56)

        uq = User.objects.annotate(
            first_th_valid_from=Min('tariff_history__valid_from', filter=Q(
                tariff_history__valid_until__lte=today,
                tariff_history__is_active=True,
                tariff_history__tariff__tariff_group__is_wave=True,
            ))
        ).filter(
            tariff_history__valid_from__lte=today,
            tariff_history__valid_until__gte=today,
            tariff_history__tariff__tariff_group__is_wave=True,
            tariff_history__is_active=True,
            first_th_valid_from__gte=start_date,
            first_th_valid_from__lt=end_date,
        )

        uq = uq.order_by('id').all()
        return self.filter_already_created_notifications(uq)

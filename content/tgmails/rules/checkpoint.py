from datetime import timedelta

from django.conf import settings
from django.db.models import F, Q, Exists, OuterRef

from content.tgmails.base import IMailing
from content.tgmails.sendmail import sender
from srbc.models import User
from crm.models import TariffHistory

__all__ = ('CheckpointDate',)


@sender.register
class CheckpointDate(IMailing):
    SYSTEM_CODE = 'checkpoint_date'

    START_DATE = settings.CHECKPOINT_START_DATE
    CRON_HOURS = 20
    CRON_MINUTES = 20

    def get_reference_date(self):
        # Each two weeks, starting from START_DATE

        weeks_passed = (self.today - self.START_DATE).days / 7
        weeks_passed += weeks_passed % 2
        return self.START_DATE + timedelta(weeks=weeks_passed)

    def get_users(self):
        uq = User.objects

        start_notification_day = self.today - timedelta(days=7)
        end_notification_day = self.today + timedelta(days=7)

        next_th = TariffHistory.objects.filter(
            user_id=OuterRef('pk'),
            valid_from__gt=self.today,
            is_active=True,
            tariff__tariff_group__is_in_club=False,
            tariff__tariff_group__is_wave=True
        )

        uq = uq.filter(
            Q(
                # этим условием сможем отсечь новчиков, которым сразу не нужно слать
                tariff_history__valid_from__lte=start_notification_day,
                tariff_history__is_active=True,
                tariff_history__tariff__tariff_group__is_in_club=False,
                tariff_history__tariff__tariff_group__is_wave=True,
                profile__is_perfect_weight=False,
                tariff_history__valid_until__gte=self.today
            )
            &
            # этим условием сможем отсечь заканчивающих,
            # если тх ТХ осталось меньше недели, то проверяем есть ли запись после
            Q(
                Q(tariff_history__valid_until__gte=end_notification_day)
                |
                Q(
                    Q(tariff_history__valid_until__lt=end_notification_day)
                    &
                    Q(Exists(next_th))
                )
            )
        )

        uq = uq.order_by('id').all()
        return self.filter_already_created_notifications(uq)

from datetime import timedelta, date

from content.tgmails.base import IMailing
from content.tgmails.sendmail import sender
from srbc.models import User, Wave

__all__ = ('ChangeWarning', 'ChangeNotice', )


@sender.register
class ChangeWarning(IMailing):
    SYSTEM_CODE = 'meal_analyze_change_warning'

    CRON_HOURS = 9
    CRON_MINUTES = 15

    def get_reference_date(self):
        today = date.today()

        # в пятницу, в дату старта потока
        last_wave = Wave.objects.filter(
            start_date__lte=today
        ).order_by(
            '-start_date'
        ).first()

        if not last_wave:
            return None

        return last_wave.start_date

    def get_users(self):
        #  кампания участника имеет start_date = NOW - 111d
        # (или можно, на всякий случай, сделать NOW-112d < start_date < NOW-105d)
        today = date.today()

        start_date = today - timedelta(days=112)
        end_date = today - timedelta(days=105)

        uq = User.objects.filter(
            tariff_history__valid_until__gte=self.today,
            tariff_history__valid_from__lte=self.today,
            tariff_history__is_active=True,
            tariff_history__tariff__tariff_group__is_wave=True,

            application__campaign__start_date__lt=end_date,
            application__campaign__start_date__gte=start_date
        )

        uq = uq.order_by('id').all()
        return self.filter_already_created_notifications(uq)


@sender.register
class ChangeNotice(IMailing):
    SYSTEM_CODE = 'meal_analyze_change_notice'

    CRON_HOURS = 9
    CRON_MINUTES = 15

    def get_reference_date(self):
        today = date.today()

        # в пятницу, в дату старта потока
        last_wave = Wave.objects.filter(
            start_date__lte=today
        ).order_by(
            '-start_date'
        ).first()

        if not last_wave:
            return None

        return last_wave.start_date

    def get_users(self):
        # кампания участника имеет start_date = NOW - 139d
        # (или можно, на всякий случай, сделать NOW-140d < start_date < NOW-133d)
        today = date.today()

        start_date = today - timedelta(days=140)
        end_date = today - timedelta(days=133)

        uq = User.objects.filter(
            tariff_history__valid_until__gte=self.today,
            tariff_history__valid_from__lte=self.today,
            tariff_history__is_active=True,
            tariff_history__tariff__tariff_group__is_wave=True,

            application__campaign__start_date__lt=end_date,
            application__campaign__start_date__gte=start_date
        )

        uq = uq.order_by('id').all()
        return self.filter_already_created_notifications(uq)

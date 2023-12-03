from datetime import datetime, timedelta, date

from django.db.models import Max, Case, When

from content.tgmails.base import IMailing
from content.tgmails.sendmail import sender
from srbc.models import User

__all__ = ('ClubChatNoData', 'ClubChannelNoData', )


@sender.register
class ClubChatNoData(IMailing):
    SYSTEM_CODE = 'clubchat_nodata'

    CRON_HOURS = 8
    CRON_MINUTES = 15

    def get_reference_date(self):
        # Each tuesday
        today = date.today()
        return today + timedelta((1 - today.weekday()) % 7)

    def get_users(self):
        today_minus_week = (datetime.now() - timedelta(days=7)).date()
        uq = User.objects
        uq = uq.annotate(last_weight_date=Max(Case(When(diaries__weight__isnull=False, then='diaries__date'))))

        # считаем активным тариф, у которого дата окончания больше или равно сегодняшнему дню
        uq = uq.filter(
            tariff_history__valid_until__gte=self.today,
            tariff_history__valid_from__lte=self.today,
            tariff_history__is_active=True,

            tariff_history__tariff__tariff_group__communication_mode='CHAT',
            tariff_history__tariff__tariff_group__is_in_club=True,

            last_weight_date__lte=today_minus_week,
            last_weight_date__isnull=False,

            tariff_history__wave__start_date__lte=self.today
        )

        uq = uq.order_by('id').all()
        return self.filter_already_created_notifications(uq)


@sender.register
class ClubChannelNoData(IMailing):
    SYSTEM_CODE = 'clubchannel_nodata'

    CRON_HOURS = 8
    CRON_MINUTES = 15

    def get_reference_date(self):
        # Each tuesday
        today = date.today()
        return today + timedelta((1 - today.weekday()) % 7)

    def get_users(self):
        today_minus_week = (datetime.now() - timedelta(days=7)).date()
        uq = User.objects
        uq = uq.annotate(last_weight_date=Max(Case(When(diaries__weight__isnull=False, then='diaries__date'))))

        # считаем активным тариф, у которого дата окончания больше или равно сегодняшнему дню
        uq = uq.filter(
            tariff_history__valid_until__gte=self.today,
            tariff_history__valid_from__lte=self.today,
            tariff_history__is_active=True,

            tariff_history__tariff__tariff_group__communication_mode='CHANNEL',
            tariff_history__tariff__tariff_group__is_in_club=True,

            last_weight_date__lte=today_minus_week,
            last_weight_date__isnull=False,

            tariff_history__wave__start_date__lte=self.today
        )

        uq = uq.order_by('id').all()
        return self.filter_already_created_notifications(uq)

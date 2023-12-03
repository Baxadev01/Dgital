from datetime import timedelta, date

from content.tgmails.base import IMailing
from content.tgmails.sendmail import sender
from srbc.models import User, Wave

__all__ = ('ClubChatExpires',)


@sender.register
class ClubChatExpires(IMailing):
    SYSTEM_CODE = 'clubchat_expires'
    CRON_DAYS_DELTA = -15
    CRON_HOURS = 12
    CRON_MINUTES = 5

    def get_reference_date(self):
        # пока отключаем эту рассылку
        return None

        # 15 days before start of each wave
        next_wave = Wave.objects.filter(start_date__gte=date.today()).order_by('-start_date').first()

        if not next_wave:
            return None

        return next_wave.start_date + timedelta(days=self.CRON_DAYS_DELTA)

    def get_users(self):
        valid_until = self.today + timedelta(weeks=2)

        uq = User.objects
        uq = uq.filter(
            profile__active_tariff_history__valid_until__lte=valid_until,
            profile__active_tariff_history__tariff__tariff_group__communication_mode='CHAT',
            profile__active_tariff_history__tariff__tariff_group__is_in_club=True,
            profile__active_tariff_history__wave__start_date__lte=self.today
        )

        uq = uq.order_by('id').all()
        return self.filter_already_created_notifications(uq)

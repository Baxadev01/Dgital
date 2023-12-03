from datetime import datetime, timedelta, date

from content.tgmails.base import IMailing, CampaingRelatedIMailing
from content.tgmails.sendmail import sender
from crm.models import Campaign
from srbc.models import User

__all__ = ('StartPaymentReminder',)


@sender.register
class StartPaymentReminder(CampaingRelatedIMailing):
    SYSTEM_CODE = 'start_payment_reminder'

    CRON_DAYS_DELTA = -3
    CRON_HOURS = 10
    CRON_MINUTES = 20

    def get_users(self):
        today = date.today()

        uq = super(StartPaymentReminder, self).get_inactive_users()

        uq = uq.filter(application__admission_status='ACCEPTED')
        uq = uq.filter(application__is_payment_allowed=True)

        uq = uq.filter(
            application__tariff__isnull=False,
            application__tariff__tariff_group__communication_mode='CHANNEL'
        )

        return self.filter_already_created_notifications(uq)

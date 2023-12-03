from datetime import timedelta, date

from content.tgmails.base import IMailing
from content.tgmails.sendmail import sender
from srbc.models import User, Subscription

__all__ = ('SubscriptionRenewalWarning', )


@sender.register
class SubscriptionRenewalWarning(IMailing):
    SYSTEM_CODE = 'subscription_renewal_warning'

    CRON_HOURS = 9
    CRON_MINUTES = 15

    def get_users(self):
        today = date.today()

        end_date = today + timedelta(days=7)

        uq = User.objects.filter(
            subscriptions__status=Subscription.STATUS_ACTIVE,
            subscriptions__payments__tariff_history__valid_until=end_date,
            subscriptions__payments__tariff_history__valid_from__lte=self.today,
            subscriptions__payments__tariff_history__is_active=True,
            subscriptions__payments__tariff_history__tariff__tariff_group__is_wave=False,
            profile__next_tariff_history__isnull=True
        )

        uq = uq.order_by('id').all()
        return self.filter_already_created_notifications(uq)

    def get_fingerprint_code(self):
        return 'subscription_warning'

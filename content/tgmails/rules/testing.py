from content.tgmails.base import CampaingRelatedIMailing
from content.tgmails.sendmail import sender

__all__ = ('TestingStart', 'TestingEnd',)


@sender.register
class TestingStart(CampaingRelatedIMailing):
    SYSTEM_CODE = 'testing_start'
    CRON_DAYS_DELTA = -14
    CRON_HOURS = 7
    CRON_MINUTES = 55

    def get_users(self):

        uq = super(TestingStart, self).get_inactive_users()

        uq = uq.filter(
            application__tariff__isnull=False,
            application__tariff__tariff_group__communication_mode='CHANNEL'
        )

        return self.filter_already_created_notifications(uq)

    def get_text_for_user(self, user):
        """

        :param user: пользователь - получатель уведомления
        :type user: django.contrib.auth.models.User
        :rtype: basestring
        """

        template = self.template

        template = template.replace('TEST_END_DATE', '%s' % user.application.campaign.admission_end_date)

        return template


@sender.register
class TestingEnd(CampaingRelatedIMailing):
    SYSTEM_CODE = 'testing_end'

    CRON_DAYS_DELTA = -8
    CRON_HOURS = 7
    CRON_MINUTES = 55

    def get_users(self):

        uq = super(TestingEnd, self).get_inactive_users()

        uq = uq.filter(
            application__tariff__isnull=False,
            application__tariff__tariff_group__communication_mode='CHANNEL'
        )
        uq = uq.filter(application__admission_status__in=['NOT_STARTED', 'IN_PROGRESS', ])

        return self.filter_already_created_notifications(uq)

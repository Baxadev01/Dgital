# -*- coding: utf-8 -*-

import abc
import logging
from datetime import date, timedelta, datetime

import six
from django.utils import timezone
from django.utils.functional import cached_property
from uuid import uuid5, UUID


from content.models import TGNotificationTemplate, TGNotification
from crm.models import Campaign
from srbc.models import User

__all__ = ('IMailing',)

logger = logging.getLogger(__name__)

NAMESPACE = UUID('85be1569-879b-4720-88dc-6f388cf54147')


@six.add_metaclass(abc.ABCMeta)
class IMailing(object):
    SYSTEM_CODE = None
    CRON_DAYS_DELTA = 0
    CRON_HOURS = 0
    CRON_MINUTES = 0

    def __init__(self):
        self.namespace_system_code = uuid5(NAMESPACE, self.SYSTEM_CODE)
        self.fingerprint = self._generate_fingerprint()

    def get_fingerprint_code(self):
        return self.SYSTEM_CODE

    def _generate_fingerprint(self, key=None):
        if key is None:
            key = str(self.today)

        _hash = str(uuid5(self.namespace_system_code, key).hex)
        return 'tgm_%s_%s' % (self.get_fingerprint_code(), _hash)

    def get_reference_date(self):
        return date.today() + timedelta(days=self.CRON_DAYS_DELTA)

    def can_mail_now(self):
        """
        :rtype: bool
        """

        ref_date = self.get_reference_date()

        if ref_date is None:
            return False

        now = datetime.now()

        discard = timedelta(
            minutes=now.minute % 5,
            seconds=now.second,
            microseconds=now.microsecond
        )
        now -= discard

        ref_time = datetime(
            day=ref_date.day, month=ref_date.month, year=ref_date.year,
            hour=self.CRON_HOURS, minute=self.CRON_MINUTES, second=0, microsecond=0
        )

        return now == ref_time

    @abc.abstractmethod
    def get_users(self):
        """
        :rtype: django.db.models.query.QuerySet
        """
        pass

    def get_text_for_user(self, user):
        """

        :param user: пользователь - получатель уведомления
        :type user: django.contrib.auth.models.User
        :rtype: basestring
        """
        return self.template

    def filter_already_created_notifications(self, qs):
        """
        :param qs: Users QuerySet
        :type qs: django.db.models.query.QuerySet
        :rtype: django.db.models.query.QuerySet
        """

        already_sent = TGNotification.objects.filter(
            fingerprint__startswith=self.fingerprint
        ).values_list('user_id', flat=True)

        qs = qs.exclude(
            pk__in=already_sent
        )

        return qs

    def get_general_template_changes(self):
        return {}

    @property
    def now(self):
        """
        :rtype: datetime.datetime
        """
        return timezone.now()

    @property
    def today(self):
        """
        :rtype: date
        """
        return date.today()

    @cached_property
    def template(self):
        """
        :rtype: basestring
        """
        try:
            text = TGNotificationTemplate.objects.get(system_code=self.SYSTEM_CODE).text
        except TGNotificationTemplate.DoesNotExist:
            logger.error('Need to create TGNotificationTemplate for system_code "%s"' % self.SYSTEM_CODE)
            raise exc

        text_to_change = self.get_general_template_changes()

        for key in text_to_change:
            text = text.replace(key, text_to_change[key])

        return text

    def __repr__(self):
        return self.SYSTEM_CODE


class CampaingRelatedIMailing(IMailing):
    campaign_to_use = None

    def __init__(self):
        super(CampaingRelatedIMailing, self).__init__()

        upcoming_campaign_start_date = date.today() - timedelta(days=self.CRON_DAYS_DELTA)
        self.campaign_to_use = Campaign.objects.filter(start_date__exact=upcoming_campaign_start_date).first()

    def get_reference_date(self):
        if self.campaign_to_use is None:
            return None

        return self.campaign_to_use.start_date + timedelta(days=self.CRON_DAYS_DELTA)

    def get_users_base(self):
        uq = User.objects
        uq = uq.filter(application__campaign=self.campaign_to_use)
        uq = uq.order_by('id').all()

        return uq

    def get_users(self):
        return self.get_users_base()

    def get_inactive_users(self):
        uq = self.get_users_base()

        uq = uq.filter(profile__active_tariff_history__isnull=True)

        return uq

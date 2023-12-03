
import logging
from datetime import date, timedelta
from django.utils import dateformat

from crm.models import Campaign, RenewalRequest
from content.tgmails.base import IMailing
from content.tgmails.sendmail import sender
from srbc.models import User, Wave, TariffGroup

logger = logging.getLogger(__name__)

__all__ = ('RenewalIgnore',)


@sender.register
class RenewalIgnore(IMailing):
    SYSTEM_CODE = 'renewal_last_warning'

    CRON_HOURS = 8
    CRON_MINUTES = 50

    def get_reference_date(self):
        # Каждые четыре недели, в пятницу, через неделю после старта (D+7d)
        # Каждые четыре недели, во вторник, через одиннадцать дней после старта (D+11d)
        # Каждые четыре недели, в пятницу через четырнадцать дней после старта (D+14d)
        # Каждые четыре недели, в понедельник через семнадцать дней после старта (D+17d)
        today = date.today()

        days_delta = [7, 11, 14, 17]

        # находим последнюю стартовавшую кампанию
        # по сути нам надо послать юзерам, у кого истекает подписка от старта прошлой волны,
        # но индикатором расслки исходим от последней кампании
        campaign = Campaign.objects.filter(
            start_date__lte=today
        ).order_by(
            '-start_date'
        ).first()

        if not campaign:
            return None

        days_from_start = (today - campaign.start_date).days

        delta = next((item for item in days_delta
                      if item >= days_from_start), None)

        if not delta:
            return None

        return campaign.start_date + timedelta(days=delta)

    def get_users(self):
        today = date.today()

        last_wave = Wave.objects.filter(
            start_date__lte=today
        ).order_by(
            '-start_date'
        ).first()

        # находим пользователей, которые уже отправили заявки
        last_start_date = last_wave.start_date
        renewal_qs = RenewalRequest.objects.filter(
            date_added__date__gte=last_start_date
        ).values_list('user_id', flat=True)

        # находим всех пользователей, у которых скоро истечет ТХ и кому открыта оплата
        # исключаем тех, кто уже подавал заявку
        uq = User.objects.filter(
            profile__active_tariff_history__valid_until__lte=today + timedelta(weeks=4),
            profile__active_tariff_history__tariff__tariff_group__communication_mode=TariffGroup.COMMUNICATION_MODE_CHANNEL,
            profile__tariff_next__isnull=False
        ).exclude(
            pk__in=renewal_qs
        )

        uq = uq.order_by('id').all()
        return self.filter_already_created_notifications(uq)

    def get_general_template_changes(self):
        campaign = Campaign.objects.filter(
            start_date__lte=date.today()
        ).order_by(
            '-start_date'
        ).first()

        #  17 дней от даты ближайшего прошлого старта
        end_date = campaign.start_date + timedelta(days=17)

        return {
            'RENEWAL_NOTICE_DATE': dateformat.format(end_date, 'j E')
        }

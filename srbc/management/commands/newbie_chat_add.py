from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef, Q

from content.models import TGChatParticipant, TGNotificationTemplate, TGNotification
from crm.models import TariffHistory, Campaign


class Command(BaseCommand):
    help = "отправляет ссылки на инвайт все новичкам"

    def handle(self, *args, **options):

        template_system_code = 'newbie_chat_add'  # FIXME
        invite_url_template = "https://t.me/joinchat/%s"

        today = date.today()
        started_min_date = today + timedelta(days=-2)
        future_max_date = today + timedelta(days=3)

        # находим, есть ли кампания чья дата старта
        # или в будущем в пределах 3х дней
        # или в прошлом в пределах 2х дней
        campaign = Campaign.objects.filter(
            Q(
                start_date__gte=today,
                start_date__lte=future_max_date
            )
            |
            Q(
                start_date__lt=today,
                start_date__gte=started_min_date
            )
        ).first()

        if not campaign:
            print('Active campaign not fount')
            return

        check_date = campaign.start_date + timedelta(days=2)

        # проверяем есть ли уже юзер в чате
        is_in_chat = TGChatParticipant.objects.filter(
            user_id=OuterRef('user_id'),
            chat_id=OuterRef('wave__starting_chat_id')
        )

        records = TariffHistory.objects.filter(
            valid_from__lte=check_date,
            valid_until__gte=check_date,
            tariff__tariff_group__is_wave=True,
            is_active=True,
            user__application__campaign=campaign
        ).select_related(
            'user', 'wave__starting_chat'
        ).annotate(
            is_in_chat=Exists(is_in_chat)
        ).all()

        tpl = TGNotificationTemplate.objects.get(system_code=template_system_code)

        for record in records:
            if not record.is_in_chat:
                # добавление
                new_participant = TGChatParticipant(
                    user=record.user,
                    chat=record.wave.starting_chat,
                    status=TGChatParticipant.STATUS_ALLOWED
                )

                new_participant.save()

                # отсылка
                tgm_fingerprint = 'newbie_chat_add_%s' % record.wave.starting_chat_id

                url = invite_url_template % record.wave.starting_chat.tg_slug

                TGNotification(
                    user_id=record.user.pk,
                    content=tpl.text.replace('INVITE_URL', '%s' % url),
                    fingerprint=tgm_fingerprint,
                    status=TGNotification.STATUS_PENDING
                ).save()

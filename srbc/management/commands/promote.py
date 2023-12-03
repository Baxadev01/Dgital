from datetime import date
from builtins import str as text

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Exists, OuterRef, Q

from content.models import TGChat, TGChatParticipant, TGNotification, TGNotificationTemplate
from crm.models import Campaign
from srbc.models import TariffGroup


class Command(BaseCommand):
    help = "Выдает доступы пользователям к чатам и каналам"

    def handle(self, *args, **options):

        template_system_code = 'user_chat_add'
        invite_url_template = "https://t.me/joinchat/%s"

        tpl = TGNotificationTemplate.objects.get(system_code=template_system_code)

        # находим всех активных юзеров
        today = date.today()

        campaign_starting = Campaign.objects.filter(
            start_date=today
        ).first()

        if not campaign_starting:
            return

        # будет искать только юзеров, чьи записи стартуют сегодня или стартанули в пределах 2 дней
        active_users = User.objects.filter(
            tariff_history__valid_from__lte=today,
            # tariff_history__valid_from__gte=min_date,
            tariff_history__valid_until__gt=today,
            tariff_history__is_active=True,
            tariff_history__tariff__tariff_group__is_wave=True,
            is_staff=False,
            application__campaign__start_date__lte=today
        ).all()

        active_chat_c = TGChat.objects.filter(
            code__istartswith="C",
            is_active=True
        ).order_by('-start_date').first()

        active_chat_ad = TGChat.objects.filter(
            code__istartswith="AD",
            is_active=True
        ).order_by('-start_date').first()

        if not active_chat_c or not active_chat_ad:
            print('нет нужных активных чатов..')
            return

        in_club_users = []

        for user in active_users:
            chats_to_add = []
            print(user)
            # пользователей, которые не в клубе - заблокировать доступ к чатам, начинающимся с C и AD
            if not user.profile.is_in_club:
                print('Not in club')
                tgcp_to_ban = TGChatParticipant.objects.filter(
                    Q(user=user, chat__is_active=True)
                    &
                    Q(
                        Q(chat__code__istartswith="C") | Q(chat__code__istartswith="AD")
                    )
                ).all()

                for _record in tgcp_to_ban:
                    _record.status = TGChatParticipant.STATUS_BANNED
                    _record.save(update_fields=['status'])

                    LogEntry.objects.log_action(
                        user_id=settings.SYSTEM_USER_ID,
                        content_type_id=ContentType.objects.get_for_model(_record).pk,
                        object_id=_record.pk,
                        object_repr=text(_record.user.profile),
                        action_flag=CHANGE,
                        change_message="promote, not in club"
                    )

                # проверить, если он не является участником соответствующего next_chat - добавить его участником туда и отправить ссылку на присоединение
                next_chats = TGChat.objects.filter(
                    Q(is_active=True,
                      next_chat__isnull=False,
                      membership__user=user,
                      membership__status=TGChatParticipant.STATUS_JOINED
                      )
                    & ~Q(Exists(TGChatParticipant.objects.filter(
                        user=OuterRef('membership__user'),
                        chat=OuterRef('next_chat')
                    )))
                ).values('next_chat_id', 'next_chat__tg_slug').distinct('next_chat_id').all()
                if next_chats:
                    chats_to_add = [
                        {"chat_id": item['next_chat_id'], "slug": item['next_chat__tg_slug']} for item in next_chats
                    ]

                print('next chats:')
                print(chats_to_add)

            else:
                print('In club')
                in_club_users.append(user)

                # пользователей, которые в клубе - разблокировать заблокированные доступы к активным чатам,
                # начинающимся с C и AD
                TGChatParticipant.objects.filter(
                    Q(user=user, chat__is_active=True, status=TGChatParticipant.STATUS_BANNED)
                    &
                    Q(
                        Q(chat__code__istartswith="C") | Q(chat__code__istartswith="AD")
                    )
                ).update(status=TGChatParticipant.STATUS_ALLOWED)

                # проверить, если он не является участником соответствующего next_chat -
                # добавить его участником туда и отправить ссылку на присоединение
                if user.profile.communication_mode == TariffGroup.COMMUNICATION_MODE_CHAT:
                    print('Chat')
                    # пользователи CHAT + CLUB - отрабатывать это правило только для чатов,
                    # код которых начинается на C и G
                    next_chats = TGChat.objects.filter(
                        Q(
                            is_active=True,
                            next_chat__isnull=False,
                        )
                        &
                        Q(
                            Q(code__istartswith="C") | Q(code__istartswith="G")
                        )
                        & Q(
                            membership__user=user,
                            membership__status=TGChatParticipant.STATUS_JOINED
                        )
                        & ~Q(Exists(TGChatParticipant.objects.filter(
                            user=OuterRef('membership__user'),
                            chat=OuterRef('next_chat')
                        )))
                    ).values('next_chat_id', 'next_chat__tg_slug').distinct('next_chat_id').all()

                    if next_chats:
                        chats_to_add = [{"chat_id": item['next_chat_id'], "slug": item['next_chat__tg_slug']} for item
                                        in next_chats]

                    # пользователи CHAT + CLUB - если не является участником ни одного чата с кодом,
                    # начинающимся на C - добавить к активному C-чату
                    is_C_chat_member = TGChatParticipant.objects.filter(
                        user=user,
                        chat__is_active=True,
                        chat__code__istartswith="C"
                    ).exists()

                    if not is_C_chat_member:
                        chats_to_add.append({"chat_id": active_chat_c.pk, "slug": active_chat_c.tg_slug})

                    print('next chats:')
                    print(chats_to_add)

                elif user.profile.communication_mode == TariffGroup.COMMUNICATION_MODE_CHANNEL:
                    print('Channel')
                    # пользователи CHANNEL + CLUB - если не является участником ни одного активного чата с кодом,
                    # начинающимся на AD - добавить к активному AD-чату
                    is_AD_chat_member = TGChatParticipant.objects.filter(
                        user=user,
                        chat__is_active=True,
                        chat__code__istartswith="AD"
                    ).exists()

                    if not is_AD_chat_member:
                        chats_to_add.append({"chat_id": active_chat_ad.pk, "slug": active_chat_ad.tg_slug})

                    print('next chats:')
                    print(chats_to_add)

            # инвайтим в чат
            for chat in chats_to_add:
                # добавление
                TGChatParticipant(
                    user=user,
                    chat_id=chat['chat_id'],
                    status=TGChatParticipant.STATUS_ALLOWED
                ).save()

                # отсылка
                tgm_fingerprint = 'user_chat_add_%s' % chat['chat_id']
                url = invite_url_template % chat['slug']

                TGNotification(
                    user_id=user.pk,
                    content=tpl.text.replace('INVITE_URL', '%s' % url),
                    fingerprint=tgm_fingerprint,
                    status=TGNotification.STATUS_PENDING
                ).save()

        # return

        # все активные чаты, у которых есть next_chat пометить в системе неактивными
        TGChat.objects.filter(is_active=True, next_chat__isnull=False).update(is_active=False)

        # пользователей на тарифе В КЛУБЕ заблокировать во всех АКТИВНЫХ чатах кроме начинающихся на C, G, AD
        tgcp_to_ban = TGChatParticipant.objects.filter(
            Q(user__in=in_club_users, chat__is_active=True)
            &
            ~Q(
                Q(chat__code__istartswith="C")
                | Q(chat__code__istartswith="AD")
                | Q(chat__code__istartswith="IM")
                | Q(chat__code__istartswith="G")
            )
        ).all()

        for _record in tgcp_to_ban:
            _record.status = TGChatParticipant.STATUS_BANNED
            _record.save(update_fields=['status'])

            LogEntry.objects.log_action(
                user_id=settings.SYSTEM_USER_ID,
                content_type_id=ContentType.objects.get_for_model(_record).pk,
                object_id=_record.pk,
                object_repr=text(_record.user.profile),
                action_flag=CHANGE,
                change_message="promote, in club"
            )

        print('finish')

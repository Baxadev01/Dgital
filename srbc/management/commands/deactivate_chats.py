# -*- coding: utf-8 -*-
import logging
from builtins import str as text
from datetime import date

from django.conf import settings
from django.contrib.admin.models import LogEntry, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db.models import Q, Exists, OuterRef

from crm.models import TariffHistory
from srbc.models import User
from content.models import TGChatParticipant

logger = logging.getLogger(__name__)
system_user = settings.SYSTEM_USER_ID


class Command(BaseCommand):
    help = "Deactivates expired users"

    def add_arguments(self, parser):
        parser.add_argument('user', type=int, nargs='?', default=None)

    def handle(self, *args, **options):
        user_id = options.get('user', None)

        today = date.today()

        users = User.objects
        if user_id:
            users = users.filter(pk=user_id)

        users = users.filter(
            Q(is_staff=False)
            &
            ~Q(
                Exists(
                    TariffHistory.objects.filter(
                        user_id=OuterRef('pk'),
                        valid_until__gte=today,
                        valid_from__lte=today,
                        is_active=True,
                        tariff__tariff_group__is_wave=True
                    )
                )
            )
            & Q(
                Exists(
                    TGChatParticipant.objects.filter(
                        Q(user_id=OuterRef('pk'), chat__is_active=True)
                        &
                        ~Q(status=TGChatParticipant.STATUS_BANNED)
                    )
                )
            )
        ).all()

        for _user in users:

            log_msg = 'Deactivating user chats %s (#%s)' % (_user.username, _user.pk)
            change_message = 'chats and channels banned'

            _user.profile.deactivate()

            print(log_msg)
            logger.info(log_msg)

            LogEntry.objects.log_action(
                user_id=system_user,
                content_type_id=ContentType.objects.get_for_model(_user.profile).pk,
                object_id=_user.profile.id,
                object_repr=text(_user.profile),
                action_flag=CHANGE,
                change_message=change_message
            )

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
            Q(profile__tariff_next__isnull=False)
            &
            ~Q(Exists(
                TariffHistory.objects.filter(
                    user_id=OuterRef('pk'),
                    valid_until__gte=today,
                    valid_from__lte=today,
                    is_active=True,
                    tariff__tariff_group__is_wave=True
                )
            )
            )
        ).annotate(
            exist_tf=Exists(
                TariffHistory.objects.filter(
                    user_id=OuterRef('pk'),
                    is_active=True,
                    tariff__tariff_group__is_wave=True
                )
            )
        ).all()

        for _user in users:
            if _user.exist_tf:
                log_msg = 'Deactivating user %s (#%s)' % (_user.username, _user.pk)
                change_message = 'Payment canceled (deactivation)'
            else:
                log_msg = 'Deactivating newcomer user %s (#%s)' % (_user.username, _user.pk)
                change_message = 'Payment canceled (new user deactivation)'

            print(log_msg)
            logger.info(log_msg)

            _user.profile.tariff_next = None
            _user.profile.save(update_fields=['tariff_next', ])

            LogEntry.objects.log_action(
                user_id=system_user,
                content_type_id=ContentType.objects.get_for_model(_user.profile).pk,
                object_id=_user.profile.id,
                object_repr=text(_user.profile),
                action_flag=CHANGE,
                change_message=change_message
            )

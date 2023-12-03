# -*- coding: utf-8 -*-
from __future__ import print_function

import logging
from datetime import date
from datetime import timedelta

from django.core.management.base import BaseCommand

from content.models import TGNotificationTemplate, TGNotification
from srbc.models import User, UserReport
from srbc.tasks import _generate_results_report

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate final stat for leaving users"

    def add_arguments(self, parser):
        parser.add_argument('user', type=int, nargs='?', default=None)

    def handle(self, *args, **options):
        tgm_template_code = 'final_stat'
        use_date = date.today()

        tgm_fingerprint = 'finalstat_%s' % use_date

        valid_until_next = date.today() + timedelta(days=3)
        users = User.objects

        user_id = options.get('user', None)
        existing_messages = TGNotification.objects.filter(fingerprint=tgm_fingerprint).values_list('user_id', flat=True)

        if user_id:
            users = users.filter(pk=user_id)
        else:
            users = users.filter(
                tariff_history__valid_until__lte=valid_until_next,
                tariff_history__valid_until__gte=use_date,
                tariff_history__valid_from__lte=use_date,
                tariff_history__is_active=True,
                tariff_history__tariff__tariff_group__is_wave=True,
            ).exclude(
                tariff_history__valid_until__gte=valid_until_next,
                tariff_history__is_active=True,
                tariff_history__tariff__tariff_group__is_wave=True,
            )

        users = users.exclude(pk__in=existing_messages)

        users = users.all()

        print("Users to process: %s" % len(users))
        tpl = TGNotificationTemplate.objects.get(system_code=tgm_template_code)

        for _u in users:
            print("User #%s (%s)" % (_u.id, _u.username))
            report = UserReport.objects.filter(user_id=_u.pk, date=use_date).first()
            if report is None:
                report = UserReport(
                    date=date.today(),
                    user=_u
                )

                report.save()

            if not report.pdf_file:
                # ставим задачу на подсчет отчета
                try:
                    _generate_results_report(report)
                except Exception as e:
                    print("Error generating report for user %s: %s" % (_u.id, e))
                    continue

                if not report.pdf_file:
                    print("Error generating report for user %s" % _u.id)
                    continue

            pdf_url = "https://static.selfreboot.camp/reports/%s/%s.pdf" % (
                report.date.strftime('%Y-%m-%d'),
                report.hashid,
            )

            TGNotification(
                user_id=_u.pk,
                content=tpl.text % pdf_url,
                fingerprint=tgm_fingerprint,
                status='PENDING'
            ).save()

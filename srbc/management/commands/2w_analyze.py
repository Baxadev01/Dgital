# -*- coding: utf-8 -*-
import json
import logging
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from django_telegrambot.apps import DjangoTelegramBot
from telegram.utils.helpers import escape_markdown

from content.models import AnalysisTemplate
from srbc.models import User, DiaryRecord, UserNote, Profile, TariffGroup

logger = logging.getLogger(__name__)


def replace_vars(user, text):
    # TODO тут не упадет, если NONE ?
    text_upd = text.replace('[ENDDATE]', user.profile.valid_until.strftime("%d.%m.%Y"))
    return text_upd


def add_usernote_by_template(user, template_id):
    template_to_use = AnalysisTemplate.objects.filter(system_code=template_id).first()
    if not template_to_use:
        logger.exception('Template %s for auto-analisys not found (user %s)!' % (template_id, user.pk))
        return

    last_usernote = UserNote.objects.filter(user=user, label='IG', is_published=True).order_by('-date_added').first()

    text = replace_vars(user=user, text=template_to_use.text)

    note = UserNote(
        user=user,
        author_id=settings.SYSTEM_USER_ID,
        label='IG',
        date_added=timezone.now(),
        content=text,
        is_published=True
    )

    if last_usernote:
        note.adjust_calories = last_usernote.adjust_calories
        note.adjust_protein = last_usernote.adjust_protein
        note.add_fat = last_usernote.add_fat
        note.adjust_fruits = last_usernote.adjust_fruits
        note.adjust_carb_bread_min = last_usernote.adjust_carb_bread_min
        note.adjust_carb_bread_late = last_usernote.adjust_carb_bread_late
        note.adjust_carb_carb_vegs = last_usernote.adjust_carb_carb_vegs
        note.adjust_carb_mix_vegs = last_usernote.adjust_carb_mix_vegs

        note.adjust_carb_sub_breakfast = last_usernote.adjust_carb_sub_breakfast
        note.exclude_lactose = last_usernote.exclude_lactose
        note.restrict_lactose_casein = last_usernote.restrict_lactose_casein

    note.save()


class Command(BaseCommand):
    help = "Creating regular analysis record for some users"

    def add_arguments(self, parser):
        parser.add_argument('user', type=int, nargs='?', default=None)

    def handle(self, *args, **options):
        user_id = options.get('user', None)

        today = date.today()
        today_minus_7 = today - timedelta(days=6)

        users = User.objects.filter(
            is_staff=False,

            tariff_history__is_active=True,
            tariff_history__valid_from__lte=today,
            tariff_history__valid_until__gte=today,
            tariff_history__tariff__tariff_group__diary_analyze_mode=TariffGroup.DIARY_ANALYZE_AUTO,

            # tariff_history__tariff__tariff_group__is_in_club=False,
            # tariff_history__tariff__tariff_group__is_wave=True,

            tariff_history__wave__start_date__lt=today_minus_7
        ).select_related('profile')

        note_qs = UserNote.objects.filter(
            label='IG',
            user_id=OuterRef("pk")
        ).order_by("-date_added")

        users = users.annotate(
            last_note=Subquery(note_qs.values('date_added')[:1])
        ).select_related('profile', 'profile__group_leader')

        users = users.filter(last_note__lte=today_minus_7)

        if user_id:
            users = users.filter(pk=user_id)

        users = users.all()

        users_to_check = []

        stat = {
            'no_data': 0,
            'partial_data': 0,
            'ooc_weight_down': 0,
            'ooc_weight_up': 0,
            'fab': 0,
            'manual': 0,
            'manual_gtt': 0,
            'pr': 0,
        }

        for _user in users:
            print(("User %s (%s)" % (_user.id, _user.username)))
            days_since_start = (date.today() - _user.profile.wave.start_date).days

            if days_since_start < 21:
                print("less than 3 weeks from start")
                continue

            interval_start = date.today() - timedelta(days=date.today().weekday(), weeks=2)
            interval_end = interval_start + timedelta(days=13)

            gtt_note = UserNote.objects.filter(
                user=_user, label='DOC',
                date_added__date__gte=interval_start
            ).exists()

            # gtt_suffix = '_gtt' if gtt_note else ''

            print(("Dates: %s - %s" % (interval_start, interval_end)))
            if gtt_note:
                print("Has DOC note within last 2 weeks")
                stat['manual_gtt'] += 1
                continue

            days_to_use = DiaryRecord.objects.filter(
                user=_user,
                date__gte=interval_start, date__lte=interval_end,
                meal_status__in=['PENDING', 'DONE'],
                is_fake_meals=False,
                weight__isnull=False,
                steps__isnull=False
            )

            days_count = days_to_use.count()

            if _user.profile.meal_analyze_mode == Profile.MEAL_ANALYZE_MODE_AUTO:
                print("Meal analyze mode == AUTO")
                stat['manual'] += 1
                continue

            if days_count <= 5:
                print(("No data (%s days)" % days_count))
                add_usernote_by_template(user=_user, template_id='auto_no_data')
                stat['no_data'] += 1
                continue

            if days_count <= 9:
                print(("Partial data (%s days)" % days_count))
                add_usernote_by_template(user=_user, template_id='auto_partial_data')
                stat['partial_data'] += 1
                continue

            ooc_days = days_to_use.filter(faults__gte=3).count()
            first_weight = days_to_use.values_list('weight', flat=True).first()
            last_weight = days_to_use.values_list('weight', flat=True).last()
            if ooc_days >= 7:
                print(("OOC days: %s, first weight: %s, last weight: %s" % (ooc_days, first_weight, last_weight)))
                if first_weight > last_weight:
                    add_usernote_by_template(user=_user, template_id='auto_ooc_weight_down')
                    stat['ooc_weight_down'] += 1
                else:
                    add_usernote_by_template(user=_user, template_id='auto_ooc_weight_up')
                    stat['ooc_weight_up'] += 1

                continue

            fab_actions = sum([d.faults for d in days_to_use if d.faults is not None])

            if fab_actions > days_count:
                print(("FAB actions: %s, days with data: %s" % (fab_actions, days_count)))
                add_usernote_by_template(user=_user, template_id='auto_fab')
                stat['fab'] += 1
                continue

            days_with_pers_rec_total = days_to_use.filter(
                pers_rec_flag__in=[DiaryRecord.PERS_REC_F, DiaryRecord.PERS_REC_OK]
            ).count()
            days_with_pers_rec_ok = days_to_use.filter(pers_rec_flag__in=[DiaryRecord.PERS_REC_OK]).count()
            if days_with_pers_rec_total:
                pers_rec_actual = Decimal(days_with_pers_rec_ok) / Decimal(days_with_pers_rec_total)
            else:
                pers_rec_actual = 1

            pers_rec_min_allowed = Decimal(0.5)

            if pers_rec_actual <= pers_rec_min_allowed:
                print("Personal Recommendations matched: %s / %s" % (days_with_pers_rec_ok, days_with_pers_rec_total))
                add_usernote_by_template(user=_user, template_id='auto_pr_ignored')
                stat['pr'] += 1
                users_to_check.append(_user.pk)
                continue

            print("Manual")
            stat['manual'] += 1

            pass

        stat_json = json.dumps(stat, indent=2)

        info_msg = 'Auto Analysis results: \n\n%s' % '\n'.join(
            ['%s: %s' % (escape_markdown(k), v) for k, v in stat.items()]
        )

        DjangoTelegramBot.dispatcher.bot.send_message(
            chat_id=settings.CHATBOT_NOTIFICATION_GROUP_ID,
            text=info_msg,
            disable_web_page_preview=True,
            parse_mode='Markdown',
            timeout=5
        )

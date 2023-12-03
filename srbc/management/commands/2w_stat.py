# -*- coding: utf-8 -*-
import logging
from datetime import date, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db import connection
from django.utils import timezone
from django_telegrambot.apps import DjangoTelegramBot

from srbc.models import ProfileTwoWeekStat

logger = logging.getLogger(__name__)


def fill_statistics(start_date, end_date):
    """ Fill statistics for each user from [TODAY - start_days_offset] to [TODAY - end_days_offset]

    :param start: start days offset
    :type start: int
    :param end: end days offset
    :type end: int
    :return: True - if transaction is done, False - in case of errors
    :rtype: bool
    """
    result = True
    with connection.cursor() as cursor:
        try:
            cursor.execute(RAW_SQL, {'start': start_date, 'end': end_date})
        except IntegrityError as e:
            result = False
            #Exceptions do not have message attribute in Python 3
            #logger.error(e.message)
            logger.error(e)

    return result


class Command(BaseCommand):
    # SRBC-23
    help = "Fills statistics for regular analyse (srbc.ProfileTwoWeekStat)"

    def handle(self, *args, **options):
        # Скрипт должен собирать статистику каждые две недели не раньше вторника.
        today = timezone.now().date()

        periods_passed = (today - settings.ANALYSIS_DATA_START_DATE).days // 14
        last_period_start = settings.ODD_WEEK_START_DATE + timedelta(days=14 * periods_passed)
        last_period_end = last_period_start + timedelta(days=13)

        if ProfileTwoWeekStat.objects.filter(date=last_period_end).exists():
            logger.info(
                'Statistics for this period (%s - %s) already exists.' % (
                    last_period_start, last_period_end,
                )
            )
            return None

        # collect stat for 2 weeks
        is_successful = fill_statistics(start_date=last_period_start, end_date=last_period_end)
        if is_successful:
            info_msg = '2Week Statistics was successfully updated (%s - %s).' % (
                last_period_start, last_period_end,
            )
        else:
            info_msg = 'Could not generate 2 Week Statistics this time. See log for more information.'

        logger.info(info_msg)
        try:
            DjangoTelegramBot.dispatcher.bot.send_message(
                chat_id=settings.CHATBOT_NOTIFICATION_GROUP_ID,
                text=info_msg,
                disable_web_page_preview=True,
                parse_mode='Markdown',
                timeout=5
            )
        except Exception as e:
            pass


RAW_SQL = """
INSERT INTO srbc_profiletwoweekstat (
    user_id,
    date_start, trueweight_start, weight_start,
    date_end,   trueweight_end,   weight_end,
    steps_ok_days, steps_days, overcalory_days, ooc_days,
    faulty_days, meals_bad_days, meals_days, alco_days,
    date, created_at
)
SELECT DISTINCT 
       p.user_id                                  AS id,
       tw_start.date                              AS date_start,
       tw_start.trueweight                        AS trueweight_start,
       tw_start.weight                            AS weight_start,
       tw_end.date                                AS date_end,
       tw_end.trueweight                          AS trueweight_end,
       tw_end.weight                              AS weight_end,
       week_stat.steps_ok_days,
       week_stat.steps_days,
       week_stat.overcalory_days,
       week_stat.ooc_days,
       week_stat.faulty_days,
       week_stat.meals_bad_days,
       week_stat.meals_days,
       COALESCE(alco_stat.alco_days, (0)::bigint) AS alco_days,
       %(end)s                                    AS date,
       NOW()                                      AS created_at
FROM ((((srbc_profile p
    LEFT JOIN (SELECT srbc_diaryrecord.user_id,
                      srbc_diaryrecord.date,
                      srbc_diaryrecord.trueweight,
                      srbc_diaryrecord.weight,
                      row_number() OVER (PARTITION BY srbc_diaryrecord.user_id ORDER BY srbc_diaryrecord.date) AS rn
               FROM srbc_diaryrecord
               WHERE (
                        (srbc_diaryrecord.date >= %(start)s) AND
                        (srbc_diaryrecord.date <= %(end)s) AND
                        (srbc_diaryrecord.trueweight IS NOT NULL)
                     )
               ) tw_start ON ((tw_start.user_id = p.user_id)))
    LEFT JOIN (SELECT srbc_diaryrecord.user_id,
                      srbc_diaryrecord.date,
                      srbc_diaryrecord.trueweight,
                      srbc_diaryrecord.weight,
                      row_number()
                      OVER (PARTITION BY srbc_diaryrecord.user_id ORDER BY srbc_diaryrecord.date DESC) AS rn
               FROM srbc_diaryrecord
               WHERE (
                        (srbc_diaryrecord.date >= %(start)s) AND
                        (srbc_diaryrecord.date <= %(end)s) AND
                        (srbc_diaryrecord.trueweight IS NOT NULL)
                     )
               ) tw_end ON ((tw_end.user_id = p.user_id)))
    LEFT JOIN (SELECT srbc_diaryrecord.user_id,
                      count(1)                      AS measures,
                      sum(
                              CASE
                                  WHEN srbc_diaryrecord.is_overcalory THEN 1
                                  ELSE 0
                                  END)              AS overcalory_days,
                      sum(
                              CASE
                                  WHEN srbc_diaryrecord.is_ooc THEN 1
                                  ELSE 0
                                  END)              AS ooc_days,
                      sum(
                              CASE
                                  WHEN (srbc_diaryrecord.is_ooc OR (COALESCE(srbc_diaryrecord.faults, 0) > 0)) THEN 1
                                  ELSE 0
                                  END)              AS faulty_days,
                      sum(
                              CASE
                                  WHEN srbc_diaryrecord.is_ooc THEN 1
                                  WHEN srbc_diaryrecord.is_mono THEN 0
                                  WHEN srbc_diaryrecord.is_unload THEN 0
                                  WHEN srbc_diaryrecord.meals IS NULL THEN 0
                                  WHEN COALESCE(srbc_diaryrecord.meals, 0) >= 7 THEN 0
                                  ELSE 1
                                  END)              AS meals_bad_days,
                      sum(
                              CASE
                                  WHEN (srbc_diaryrecord.steps >= 8000) THEN 1
                                  ELSE 0
                                  END)              AS steps_ok_days,
                      count(srbc_diaryrecord.steps) AS steps_days,
                      sum(
                              CASE
                                  WHEN srbc_diaryrecord.meal_status IN ('PENDING', 'DONE') THEN 1
                                  ELSE 0
                                  END
                          )                         AS meals_days
               FROM srbc_diaryrecord
               WHERE (
                    srbc_diaryrecord.date >= %(start)s AND
                    srbc_diaryrecord.date <= %(end)s
               )
               GROUP BY srbc_diaryrecord.user_id) week_stat ON ((week_stat.user_id = p.user_id)))
    LEFT JOIN (SELECT dr.user_id,
                       count(DISTINCT dr.id) AS alco_days
                FROM ((srbc_diaryrecord dr
                    LEFT JOIN srbc_diarymeal dm ON ((dm.diary_id = dr.id)))
                         LEFT JOIN srbc_mealcomponent dmc ON ((dmc.meal_id = dm.id)))
                WHERE (
                    (dr.date >= %(start)s) AND
                    (dr.date <= %(end)s) AND
                    ((dmc.component_type)::text = 'alco'::text)
                )
                GROUP BY dr.user_id) alco_stat ON ((alco_stat.user_id = p.user_id)))
    JOIN crm_tariffhistory th
          ON th.valid_from <= %(end)s AND th.valid_until >= %(end)s AND th.is_active AND
            p.user_id = th.user_id
    JOIN srbc_tariff st ON th.tariff_id = st.id
    JOIN srbc_tariffgroup stg ON st.tariff_group_id = stg.id AND stg.is_wave
WHERE (tw_start.rn = 1) AND (tw_end.rn = 1);
"""

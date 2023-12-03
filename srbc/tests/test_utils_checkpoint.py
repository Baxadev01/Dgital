# -*- coding: utf-8 -*-

import datetime

from django.conf import settings
from django.test import TestCase, SimpleTestCase

from srbc.tests.factories import UserFactory, CheckpointFactory, DiaryRecordFactory
from srbc.utils.checkpoint_measurement import (get_nearest_saturday_in_past, get_nearest_saturday_in_future,
                                               get_nearest_schedule_saturday, collect_image_info)

# FIXME - тоже потом переделать
# тут и ниже все что связано с profile.is_active и profile__wave


class ImageInfo(TestCase):
    def setUp(self):
        self.user = UserFactory(profile__is_active=True, profile__is_in_club=False,
                                profile__wave__start_date=datetime.date(2018, 1, 1),
                                profile__height=180,
                                application__height=180,
                                application__weight=100,
                                )

    def generate_filled_checkpoint(self, date, user=None):
        user = user or self.user

        return CheckpointFactory(
            date=date,
            user=user,
            measurement_point_01=99,
            measurement_point_02=99,
            measurement_point_03=99,
            measurement_point_04=99,
            measurement_point_05=99,
            measurement_point_06=99,
            measurement_point_07=99,
            measurement_point_08=99,
            measurement_point_09=99,
            measurement_point_10=99,
            measurement_point_11=99,
            measurement_point_12=99,
            measurement_point_13=99,
            measurement_point_14=99,
            measurement_point_15=99,
            measurement_point_16=99,
            measurement_height=100,
            is_measurements_done=True,
            is_editable=False
        )

    def test_no_checkpoint_exists(self):
        result = collect_image_info(user=self.user, date=datetime.date(2018, 2, 3))
        self.assertIsNone(result)

    def test_no_diary_records_exists(self):
        CheckpointFactory(date=datetime.date(2018, 1, 2), user=self.user)
        DiaryRecordFactory(date=datetime.date(2018, 1, 2), user=self.user, weight=100)
        result = collect_image_info(user=self.user, date=datetime.date(2018, 2, 3))
        self.assertIsNone(result)

    def test_no_filled_checkpoints(self):
        CheckpointFactory(date=datetime.date(2018, 1, 2), user=self.user)
        DiaryRecordFactory(date=datetime.date(2018, 1, 2), user=self.user, weight=100)
        DiaryRecordFactory(date=datetime.date(2018, 1, 10), user=self.user, weight=90)
        CheckpointFactory(date=datetime.date(2018, 1, 10), user=self.user)

        result = collect_image_info(user=self.user, date=datetime.date(2018, 2, 3))
        self.assertIsNone(result)

    def test_common_work(self):
        self.generate_filled_checkpoint(date=datetime.date(2018, 1, 2))
        self.generate_filled_checkpoint(date=datetime.date(2018, 1, 10))
        DiaryRecordFactory(date=datetime.date(2018, 1, 2), user=self.user, weight=100)
        DiaryRecordFactory(date=datetime.date(2018, 1, 10), user=self.user, weight=90)

        result = collect_image_info(user=self.user, date=datetime.date(2018, 2, 3))
        self.assertIsNotNone(result)
        self.assertTrue(isinstance(result, str))


class CheckpointDate(SimpleTestCase):

    def test_exists_in_settings(self):
        # дано: CHECKPOINT_MEASUREMENT_START_DATE задает дату отсчета расписания для снятия измерений (DEV-69)
        # ожидается: в настройках должна быть прописана константа CHECKPOINT_MEASUREMENT_START_DATE
        try:
            settings.CHECKPOINT_MEASUREMENT_START_DATE

        except AttributeError:
            self.fail("You should set CHECKPOINT_MEASUREMENT_START_DATE to settings")

        except Exception:
            self.fail("You should set CHECKPOINT_MEASUREMENT_START_DATE in correct format")

    def test_get_nearest_saturdays(self):
        """
        Test logic for srbc.utils.checkpoint_measurement.get_nearest_saturday_in_past and
        srbc.utils.checkpoint_measurement.get_nearest_saturday_in_future      
        """

        # дано: srbc.utils.checkpoint_measurement.get_nearest_saturday_in_past возвращает ближайшую субботу в прошлом;
        # srbc.utils.checkpoint_measurement.get_nearest_saturday_in_future возвращает ближайшую субботу в будущем;
        # ожидается: для набора дней функция должна вернуть ближайшие субботние дни (в прошлом и будущем соотвественно);
        # разница между ними должна быть неделя (7 дней);
        # для субботы - обе функции должны вернуть тот же день

        date = datetime.datetime(2018, 1, 15)
        for n in range(35):
            _date = date + datetime.timedelta(days=n)
            _date = _date.date()
            past_saturday = get_nearest_saturday_in_past(_date)
            future_saturday = get_nearest_saturday_in_future(_date)
            self.assertEqual(past_saturday.weekday(), 5)  # 5 means saturday
            self.assertEqual(future_saturday.weekday(), 5)
            if _date.weekday() == 5:
                # для субботы должны вернуть тот же день
                self.assertEqual(past_saturday, _date)
                self.assertEqual(future_saturday, _date)
            else:
                # ближайший субботний день должен быть раньше, чем _date
                self.assertTrue(future_saturday > _date)
                # ближайший субботний день должен быть позже, чем _date
                self.assertTrue(past_saturday < _date)
                self.assertTrue((future_saturday - past_saturday).days == 7)

    def test_get_nearest_schedule_saturday(self):
        """
        Test logic for srbc.utils.checkpoint_measurement.get_nearest_schedule_saturday        
        """

        # ==== "шкала времени"
        # 2018.01.20  01.27   02.03     02.10    02.17
        # <---SD-------S-------ShS-------S`-------ShS`--->
        # где SD - CHECKPOINT_MEASUREMENT_START_DATE, S - saturday, ShS - scheduled saturday

        # дано: d < SD
        # ожидается: должен вернуться день субботы равный SD
        date = datetime.datetime(2018, 1, 15).date()
        expected_date = datetime.datetime(2018, 1, 20).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано: d << SD
        # ожидается: должен вернуться день субботы равный SD
        date = datetime.datetime(2010, 1, 15).date()
        expected_date = datetime.datetime(2018, 1, 20).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано: d = SD
        # ожидается: должен вернуться день субботы равный SD
        date = datetime.datetime(2018, 1, 20).date()
        expected_date = datetime.datetime(2018, 1, 20).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано: SD < d < S (d - SD <= 3)
        # ожидается: должен вернуться день субботы равный SD
        date = datetime.datetime(2018, 1, 22).date()
        expected_date = datetime.datetime(2018, 1, 20).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано: SD < d < S (d - SD > 3)
        # ожидается: должен вернуться день субботы равный ShS
        date = datetime.datetime(2018, 1, 24).date()
        expected_date = datetime.datetime(2018, 2, 3).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано: S = d
        # ожидается: должен вернуться день субботы равный ShS
        date = datetime.datetime(2018, 1, 27).date()
        expected_date = datetime.datetime(2018, 2, 3).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано: S < d < ShS
        # ожидается: должен вернуться день субботы равный ShS
        date = datetime.datetime(2018, 1, 30).date()
        expected_date = datetime.datetime(2018, 2, 3).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано: S < d < ShS (ShS - d <= 3)
        # ожидается: должен вернуться день субботы равный ShS
        date = datetime.datetime(2018, 2, 1).date()
        expected_date = datetime.datetime(2018, 2, 3).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано: d = ShS
        # ожидается: должен вернуться день субботы равный ShS
        date = datetime.datetime(2018, 2, 3).date()
        expected_date = datetime.datetime(2018, 2, 3).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано: ShS < d < S` ( d - ShS <= 3)
        # ожидается: должен вернуться день субботы равный ShS
        date = datetime.datetime(2018, 2, 4).date()
        expected_date = datetime.datetime(2018, 2, 3).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано: ShS < d < S` ( d - ShS > 3)
        # ожидается: должен вернуться день субботы равный ShS`
        date = datetime.datetime(2018, 2, 7).date()
        expected_date = datetime.datetime(2018, 2, 17).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано:  d = S`
        # ожидается: должен вернуться день субботы равный ShS`
        date = datetime.datetime(2018, 2, 10).date()
        expected_date = datetime.datetime(2018, 2, 17).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано:  S` < d < ShS`
        # ожидается: должен вернуться день субботы равный ShS`
        date = datetime.datetime(2018, 2, 11).date()
        expected_date = datetime.datetime(2018, 2, 17).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано:  d = ShS`
        # ожидается: должен вернуться день субботы равный ShS`
        date = datetime.datetime(2018, 2, 17).date()
        expected_date = datetime.datetime(2018, 2, 17).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано:  d > ShS` (d - ShS` <= 3)
        # ожидается: должен вернуться день субботы равный ShS`
        date = datetime.datetime(2018, 2, 18).date()
        expected_date = datetime.datetime(2018, 2, 17).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

        # дано:  d > ShS` (d - ShS` > 3)
        # ожидается: должен вернуться день субботы равный ShS``
        date = datetime.datetime(2018, 2, 21).date()
        expected_date = datetime.datetime(2018, 3, 3).date()
        result = get_nearest_schedule_saturday(date=date)
        self.assertEqual(result, expected_date)

    def test_correctness(self):
        """ get_nearest_schedule_saturday on large mapping (to be sure in correctness)
        """
        dates_mapping = {
            datetime.datetime(2018, 1, 31).date(): datetime.datetime(2018, 2, 3).date(),
            datetime.datetime(2018, 2, 1).date(): datetime.datetime(2018, 2, 3).date(),
            datetime.datetime(2018, 2, 2).date(): datetime.datetime(2018, 2, 3).date(),
            datetime.datetime(2018, 2, 3).date(): datetime.datetime(2018, 2, 3).date(),
            datetime.datetime(2018, 2, 4).date(): datetime.datetime(2018, 2, 3).date(),
            datetime.datetime(2018, 2, 5).date(): datetime.datetime(2018, 2, 3).date(),
            datetime.datetime(2018, 2, 6).date(): datetime.datetime(2018, 2, 3).date(),
            datetime.datetime(2018, 2, 7).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 8).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 9).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 10).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 11).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 12).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 13).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 14).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 15).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 16).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 17).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 18).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 19).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 20).date(): datetime.datetime(2018, 2, 17).date(),
            datetime.datetime(2018, 2, 21).date(): datetime.datetime(2018, 3, 3).date(),
        }
        for date, expected_schedule_date in list(dates_mapping.items()):
            result = get_nearest_schedule_saturday(date=date)
            self.assertEqual(
                expected_schedule_date, result,
                msg='[date] %s, [expected] %s, [got] %s' % (date, expected_schedule_date, result)
            )

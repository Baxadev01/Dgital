# -*- coding: utf-8 -*-

from django.test import TestCase, override_settings
from mock import patch
from rest_framework.test import APIRequestFactory, force_authenticate

from srbc.models import DiaryRecord
from srbc.views.api.v1.diary import DiaryRecordSet
from .factories import UserFactory

# FIXME - тоже потом переделать
# тут и ниже все что связано с profile.is_active


class TestDiaryRecordSet(TestCase):
    """
        Tests for srbc.views.api.v1.diary.DiaryRecordSet
    """

    def setUp(self):
        # FIXME - тоже потом переделать
        self.user = UserFactory(profile__is_active=True, profile__is_in_club=False)
        self.staff_user = UserFactory(profile__is_active=True, is_staff=True)
        self.payload = {'weight': 100, 'sleep': 20, 'steps': 10000}

    def create_post_request(self, payload, user_id, date, as_staff=True):
        factory = APIRequestFactory()
        url = 'api/diary/%s/%s/data/' % (user_id, date)
        request = factory.post(url, payload, format='json')
        if as_staff:
            force_authenticate(request, user=self.staff_user)
        else:
            force_authenticate(request, user=self.user)
        view = DiaryRecordSet.as_view({"post": "data_upsert"})
        return view(request, user_id, date)  # response

    def test_only_staff_access(self):
        # дано: пытаем совершить запрос от обычного юзера, а метод доступен толька для staff-а
        # ожидается: получаем ошибку 403
        response = self.create_post_request(payload={}, user_id=1, date='2017-02-02', as_staff=False)
        self.assertEqual(response.status_code, 403)

        # дано: пытаем совершить запрос от staff-юзера
        # ожидается: корректная обработка запроса (200)
        response = self.create_post_request(payload=self.payload, user_id=self.user.id, date='2017-02-02')
        self.assertEqual(response.status_code, 200)

    def test_not_existing_profile(self):
        # дано: пытаемся обновить данные для юзера, у которого нет профиля (банально неверный user_id)
        # ожидается: получаем ошибку 404
        response = self.create_post_request(payload=self.payload, user_id=10001, date='2017-02-02')
        self.assertEqual(response.status_code, 404)

    def test_wrong_payload(self):
        # дано: передали данные, которые не проходятся валидацию сериализатором
        # ожидается: должны получить ошибку 400
        bad_data = (
            {'weight': 100, 'sleep': 20, 'steps': 'foobar'},
            {'weight': 'foobar', 'sleep': 20, 'steps': 100},
            {'weight': 100, 'sleep': 'foobar', 'steps': 100},
        )
        for payload in bad_data:
            response = self.create_post_request(payload=payload, user_id=self.user.id, date='2017-02-02')
            self.assertEqual(response.status_code, 400)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    @patch('srbc.tasks.update_collages_image_info.run')
    @patch('srbc.models.Profile.update_diary_trueweight')
    def test_correct_payload(self, _update_diary_trueweight, task):
        _update_diary_trueweight.return_value = True

        # дано: добавляем данные для юзера по дате, для которой нет записи
        # ожидается:
        # 1) создается DiaryRecord и заполняется переданными данными
        # 2) данные веса не изменены (их не было раньше), поэтому update_diary_trueweight не вызывается

        # убедимся, что нет данных за такую дату
        diary_date = '2017-02-02'
        diary_record = DiaryRecord.objects.filter(user_id=self.user.id, date=diary_date).first()
        self.assertIsNone(diary_record)

        response = self.create_post_request(payload=self.payload, user_id=self.user.id, date=diary_date)
        self.assertEqual(response.status_code, 200)

        # убедимся, что запись создана и заполнена данными
        diary_record = DiaryRecord.objects.filter(user_id=self.user.id, date=diary_date).first()
        self.assertIsNotNone(diary_record)
        self.assertEqual(diary_record.weight, self.payload['weight'])
        self.assertEqual(diary_record.steps, self.payload['steps'])
        self.assertEqual(diary_record.sleep, self.payload['sleep'])

        # убедимся, что update_diary_trueweight не вызывался
        self.assertFalse(_update_diary_trueweight.called)
        self.assertFalse(task.called)

        # =======================================================

        # дано: теперь обновляем данные для записи, которая существует (но не меняем вес)
        # ожидается: вес не меняли, поэтому update_diary_trueweight не вызывается
        payload = self.payload.copy()
        payload['sleep'] = 24
        payload['steeps'] = 15000
        response = self.create_post_request(payload=payload, user_id=self.user.id, date=diary_date)
        self.assertEqual(response.status_code, 200)

        diary_record = DiaryRecord.objects.filter(user_id=self.user.id, date=diary_date).first()
        self.assertIsNotNone(diary_record)
        self.assertEqual(diary_record.weight, payload['weight'])
        self.assertEqual(diary_record.steps, payload['steps'])
        self.assertEqual(diary_record.sleep, payload['sleep'])

        # убедимся, что update_diary_trueweight не вызывался
        self.assertFalse(_update_diary_trueweight.called)
        self.assertFalse(task.called)

        # =======================================================
        # дано: теперь обновляем данные для записи, которая существует (но меняем вес)
        # ожидается: вес изменили, поэтому update_diary_trueweight должен вызваться
        payload = self.payload.copy()
        payload['weight'] = 80

        response = self.create_post_request(payload=payload, user_id=self.user.id, date=diary_date)
        self.assertEqual(response.status_code, 200)

        diary_record = DiaryRecord.objects.filter(user_id=self.user.id, date=diary_date).first()
        self.assertIsNotNone(diary_record)
        self.assertEqual(diary_record.weight, payload['weight'])
        self.assertEqual(diary_record.steps, payload['steps'])
        self.assertEqual(diary_record.sleep, payload['sleep'])

        # убедимся, что update_diary_trueweight вызывался
        self.assertTrue(_update_diary_trueweight.called)
        self.assertTrue(task.called)

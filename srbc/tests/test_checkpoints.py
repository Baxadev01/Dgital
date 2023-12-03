# -*- coding: utf-8 -*-

import datetime

from django.test import TestCase, override_settings
from mock import patch
from rest_framework.test import APIRequestFactory, force_authenticate

from srbc.models import Checkpoint
from srbc.tasks import update_collages_image_info
from srbc.tests.factories import UserFactory, CheckpointFactory
from srbc.views.api.v1.diary import CheckPointMeasurementSet

# FIXME - тоже потом переделать
# тут и ниже все что связано с profile.is_active и profile__wave


class TestUpdateCollagesImageInfoTask(TestCase):
    def setUp(self):
        self.user = UserFactory(profile__is_active=True, profile__is_in_club=False,
                                profile__wave__start_date=datetime.date(2018, 1, 1))
        self.staff_user = UserFactory(is_staff=True)

        self.checkpoint_kwargs = {"measurement_point_01": 99,
                                  "measurement_point_02": 60,
                                  "measurement_point_03": 99,
                                  "measurement_point_04": 99,
                                  "measurement_point_05": 99,
                                  "measurement_point_06": 99,
                                  "measurement_point_07": 99,
                                  "measurement_point_08": 99,
                                  "measurement_point_09": 99,
                                  "measurement_point_10": 99,
                                  "measurement_point_11": 99,
                                  "measurement_point_12": 99,
                                  "measurement_point_13": 99,
                                  "measurement_point_14": 99,
                                  "measurement_point_15": 99,
                                  "measurement_point_16": 99,
                                  "measurement_height": 99,
                                  "is_measurements_done": True,
                                  "is_editable": False}

    @override_settings(CELERY_ALWAYS_EAGER=True)
    @patch('srbc.tasks.update_collages_image_info.run')
    def test_task_called_on_checkpoint_close(self, task):
        # проверяем обычную работу алгоритма, когда таск должен быть вызван при закрытии чекпоинта (is_editable = False)

        # дано: есть редактируемый чекпоинт, делаем его НЕредактируемым
        # ожидается: должен быть вызван таск по обновлению image_info
        self.checkpoint_kwargs['is_editable'] = True

        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            checkpoint = CheckpointFactory(user=self.user, date=datetime.date(2018, 4, 16), **self.checkpoint_kwargs)
            checkpoint.save()

            # а теперь делаем чекпоинт нередактируемым по АПИ
            factory = APIRequestFactory()
            payload = {'is_editable': False}
            request = factory.patch(url, payload, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"patch": "update_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 200)
            self.assertTrue(task.called)

            checkpoint.delete()

        self.assertEqual(task.call_count, 2)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    @patch('srbc.tasks.update_collages_image_info.run')
    def test_task_not_called(self, task):
        # проверяем обычную работу алгоритма, когда таск не должен быть вызван

        editable_chkp_kwagrs = self.checkpoint_kwargs.copy()
        editable_chkp_kwagrs['is_editable'] = True

        # дано: чекпоинт редактируем
        # ожидается: не должен быть вызван таск по обновлению image_info
        checkpoint = CheckpointFactory(user=self.user, date=datetime.date(2018, 1, 1), **editable_chkp_kwagrs)
        checkpoint.save()
        self.assertFalse(task.called)

        # дано: изменили замер у РЕДАКТИРУЕМОГО чекпоинта
        # ожидается: не должен быть вызван таск по обновлению image_info
        checkpoint.measurements_point_01 = 20
        checkpoint.save()
        self.assertFalse(task.called)

        # дано: изменили дату у РЕДАКТИРУЕМОГО чекпоинта
        # ожидается: не должен быть вызван таск по обновлению image_info
        checkpoint.date = datetime.date(2018, 1, 11)
        checkpoint.save()
        self.assertFalse(task.called)

    def test_task_args_validation(self):

        # проверяем, что в таске есть проверка входных данных
        with self.assertRaises(AssertionError):
            update_collages_image_info('123')
            update_collages_image_info('123', '123')
            update_collages_image_info('123', None)
            update_collages_image_info(None, '123')
            update_collages_image_info(Checkpoint)
            update_collages_image_info(1, 2)


class TestCheckPointMeasurementSetUpsert(TestCase):
    def setUp(self):
        self.user = UserFactory(profile__is_active=True, profile__is_in_club=False,
                                profile__wave__start_date=datetime.date(2018, 1, 1))
        self.staff_user = UserFactory(is_staff=True)
        self.measurements_payload = {"measurement_point_01": 99,
                                     "measurement_point_02": 60,
                                     "measurement_point_03": 99,
                                     "measurement_point_04": 99,
                                     "measurement_point_05": 99,
                                     "measurement_point_06": 99,
                                     "measurement_point_07": 99,
                                     "measurement_point_08": 99,
                                     "measurement_point_09": 99,
                                     "measurement_point_10": 99,
                                     "measurement_point_11": 99,
                                     "measurement_point_12": 99,
                                     "measurement_point_13": 99,
                                     "measurement_point_14": 99,
                                     "measurement_point_15": 99,
                                     "measurement_point_16": 99,
                                     "measurement_height": 99}

    def test_get_measurements_200(self):
        """ Tests for successful response in srbc.views.api.v1.diary.CheckPointMeasurementSet#get_measurements"""

        # дано: у пользователя нет чекпоинтов
        # ожидается: успешный ответ с пустыми данными по чекпоинтам
        expected_data = {'checkpoints': []}

        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/', self.user, None),
            ('/api/checkpoints/%d/measurements/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            factory = APIRequestFactory()
            request = factory.get(url, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"get": "get_measurements"})
            response = view(request, user_id)

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data, expected_data)

        # =====================================================================

        # дано: у пользователя есть чекпоинты
        # ожидается: успешный ответ с данными по чекпоинтам
        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        CheckpointFactory(date=date, user=self.user)
        date = datetime.datetime.strptime('2018-04-17', '%Y-%m-%d').date()
        CheckpointFactory(date=date, user=self.user)

        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/', self.user, None),
            ('/api/checkpoints/%d/measurements/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            factory = APIRequestFactory()
            request = factory.get(url, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"get": "get_measurements"})
            response = view(request, user_id)

            self.assertEqual(response.status_code, 200)
            self.assertTrue('checkpoints' in response.data)
            self.assertEqual(len(response.data['checkpoints']), 2)

    def test_get_measurements_403(self):
        """ Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#get_measurements"""
        # дано: обычный пользователь (не стафф) пытается получить данные по чекпоинтам другого пользователя
        # ожидается: ошибка 403

        another_user = UserFactory(profile__is_active=True, profile__is_in_club=False)

        # === запрос
        factory = APIRequestFactory()
        request = factory.get('/api/checkpoints/%d/measurements/' % another_user.id, format='json')
        force_authenticate(request, user=self.user)
        view = CheckPointMeasurementSet.as_view({"get": "get_measurements"})
        response = view(request, another_user.id)

        self.assertEqual(response.status_code, 403)

    def test_get_measurement_200(self):
        """Tests for successful response in srbc.views.api.v1.diary.CheckPointMeasurementSet#get_measurement"""

        # дано: у пользователя есть чекпоинт за запрашиваемую дату
        # ожидается: успешный ответ с данными по чекпоинту
        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        CheckpointFactory(date=date, user=self.user)

        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            factory = APIRequestFactory()
            request = factory.get(url, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"get": "get_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 200)
            self.assertTrue('checkpoint' in response.data)
            self.assertIsNotNone(response.data.get('checkpoint'))

    def test_get_measurement_400(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#get_measurement"""

        # дано: в запросе передали дату в неверном формате
        # ожидается: ошибка 400

        # === запрос
        request_args = [
            # bad date
            ('/api/checkpoints/measurements/2018-04-31/', '2018-04-31', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-31/' % self.user.id, '2018-04-31', self.staff_user, self.user.id),
            # bad date format (not Y-m-d)
            ('/api/checkpoints/measurements/2018-15-01/', '2018-15-01', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-15-01/' % self.user.id, '2018-15-01', self.staff_user, self.user.id),
            ('/api/checkpoints/measurements/01-01-2018/', '01-01-2018', self.user, None),
            ('/api/checkpoints/%d/measurements/01-01-2018/' % self.user.id, '01-01-2018', self.staff_user, self.user.id),
            ('/api/checkpoints/measurements/2018.04.16', '2018.04.16', self.user, None),
            ('/api/checkpoints/%d/measurements/2018.04.16' % self.user.id, '2018.04.16', self.staff_user, self.user.id),
        ]
        for url, date, user, user_id in request_args:
            factory = APIRequestFactory()
            request = factory.get(url, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"get": "get_measurement"})
            response = view(request, date, user_id)

            self.assertEqual(response.status_code, 400)

    def test_get_measurement_403(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#get_measurement"""

        # дано: обычный пользователь (не стафф) пытается получить данные по чекпоинту другого пользователя
        # ожидается: ошибка 403
        another_user = UserFactory(profile__is_active=True, profile__is_in_club=False)
        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        CheckpointFactory(date=date, user=another_user)

        # === запрос
        factory = APIRequestFactory()
        request = factory.get('/api/checkpoints/%d/measurements/2018-04-16/' % another_user.id, format='json')
        force_authenticate(request, user=self.user)
        view = CheckPointMeasurementSet.as_view({"get": "get_measurement"})
        response = view(request, '2018-04-16', another_user.id)

        self.assertEqual(response.status_code, 403)

    def test_get_measurement_404(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#get_measurement"""

        # дано: запросили чекпоинт за дату, для которого не создан чекпоинт
        # ожидается: ошибка 404

        # === запрос
        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            factory = APIRequestFactory()
            request = factory.get(url, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"get": "get_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 404)

    def test_create_measurement_200(self):
        """Tests for successful response in srbc.views.api.v1.diary.CheckPointMeasurementSet#create_measurement"""

        # дано: пользователь создает чекпоинт за дату
        # ожидается: успешный ответ с данными по чекпоинту

        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            factory = APIRequestFactory()
            request = factory.post(url, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"post": "create_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.data.get('checkpoint'))

            date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
            checkpoint_after_request = Checkpoint.objects.filter(user=self.user, date=date).first()
            self.assertTrue(checkpoint_after_request.is_editable)
            self.assertFalse(checkpoint_after_request.is_measurements_done)

            checkpoint_after_request.delete()

    def test_create_measurement_400(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#create_measurement"""

        # дано: пользователь создает чекпоинт за дату; дата в неверном формате
        # ожидается: ошибка 400

        # === запрос
        bad_dates = [
            '2018-04-32',
            '2018-13-01',
            '2018.04.16',
            '01-01-2018'
        ]
        for bad_date in bad_dates:
            factory = APIRequestFactory()
            request = factory.post('/api/checkpoints/measurements/%s/' % bad_date, format='json')
            force_authenticate(request, user=self.user)
            view = CheckPointMeasurementSet.as_view({"post": "create_measurement"})
            response = view(request, bad_date)

            self.assertEqual(response.status_code, 400)
            self.assertEqual(list(Checkpoint.objects.filter(user=self.user)), [])

    def test_create_measurement_403(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#create_measurement"""

        # дано: обычный пользователь (не стафф) пытается создать чекпоинт другого пользователя
        # ожидается: ошибка 403
        another_user = UserFactory(profile__is_active=True, profile__is_in_club=False)

        # === запрос
        factory = APIRequestFactory()
        request = factory.post('/api/checkpoints/%d/measurements/2018-04-16/' % another_user.id, format='json')
        force_authenticate(request, user=self.user)
        view = CheckPointMeasurementSet.as_view({"post": "create_measurement"})
        response = view(request, '2018-04-16', another_user.id)

        self.assertEqual(response.status_code, 403)

    def test_create_measurement_409_date_exists(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#create_measurement"""

        # дано: пользователь создает чекпоинт за дату, но чекпоинт за запрошунную дату уже существует
        # ожидается: ошибка 409

        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        checkpoint = CheckpointFactory(date=date, user=self.user)

        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            factory = APIRequestFactory()
            request = factory.post(url, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"post": "create_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 409)
            self.assertEqual(list(Checkpoint.objects.filter(user=self.user)), [checkpoint])

    def test_create_measurement_409_editable_checkpoint_exists(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#create_measurement"""

        # дано: пользователь создает чекпоинт за незанятую дату, но у пользователя есть редактируемый чекпоинт
        # ожидается: ошибка 409

        date = datetime.datetime.strptime('2018-04-15', '%Y-%m-%d').date()
        checkpoint = CheckpointFactory(date=date, user=self.user)

        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            factory = APIRequestFactory()
            request = factory.post(url, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"post": "create_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 409)
            self.assertEqual(list(Checkpoint.objects.filter(user=self.user)), [checkpoint])

    def test_update_measurement_200__update_measurement_01(self):
        """Tests for successful response in srbc.views.api.v1.diary.CheckPointMeasurementSet#update_measurement"""

        # дано: у пользователя есть чекпоинт за запрашиваемую дату; обновляем данные замера
        # ожидается: успешный ответ с обновленными данными по чекпоинту
        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        CheckpointFactory(date=date, user=self.user, measurement_point_01=100)

        checkpoint_before_request = Checkpoint.objects.filter(user=self.user, date=date).first()
        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None, 90),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id, 80),
        ]
        for url, user, user_id, new_value in request_args:
            factory = APIRequestFactory()
            payload = {'measurement_point_01': new_value}
            request = factory.patch(url, payload, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"patch": "update_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.data.get('checkpoint'))
            self.assertEqual(response.data['checkpoint']['measurement_point_01'], new_value)

            checkpoint_after_request = Checkpoint.objects.filter(user=self.user, date=date).first()
            self.assertEqual(checkpoint_after_request.measurement_point_01, new_value)
            self.assertEqual(checkpoint_before_request.is_editable, checkpoint_after_request.is_editable)
            self.assertEqual(checkpoint_before_request.date, checkpoint_after_request.date)

    def test_update_measurement_200__update_date(self):
        """Tests for successful response in srbc.views.api.v1.diary.CheckPointMeasurementSet#update_measurement"""

        # дано: у пользователя есть чекпоинт за запрашиваемую дату; меняем дату чекпоинта
        # ожидается: успешный ответ с обновленными данными по чекпоинту
        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        CheckpointFactory(date=date, user=self.user, measurement_point_01=100)

        checkpoint_before_request = Checkpoint.objects.filter(user=self.user, date=date).first()
        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', '2018-04-16', self.user, None, '2018-04-17'),
            ('/api/checkpoints/%d/measurements/2018-04-17/' % self.user.id, '2018-04-17', self.staff_user, self.user.id,
             '2018-04-18'), ]
        for url, cur_date, user, user_id, new_date in request_args:
            factory = APIRequestFactory()
            payload = {'date': new_date}
            request = factory.patch(url, payload, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"patch": "update_measurement"})
            response = view(request, cur_date, user_id)

            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.data.get('checkpoint'))
            self.assertEqual(response.data['checkpoint']['date'], new_date)

            checkpoint_after_request = Checkpoint.objects.filter(user=self.user, date=new_date).first()
            self.assertEqual(checkpoint_after_request.date, datetime.datetime.strptime(new_date, '%Y-%m-%d').date())
            self.assertEqual(checkpoint_before_request.is_editable, checkpoint_after_request.is_editable)
            self.assertEqual(checkpoint_before_request.measurement_point_01,
                             checkpoint_after_request.measurement_point_01)

    def test_update_measurement_200__update_is_editable(self):
        """Tests for successful response in srbc.views.api.v1.diary.CheckPointMeasurementSet#update_measurement"""

        # дано: у пользователя есть чекпоинт за запрашиваемую дату (замеры заполнены); делаем чекпоинт нередактируемым
        # ожидается: успешный ответ с обновленными данными по чекпоинту

        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
            CheckpointFactory(date=date, user=self.user, **self.measurements_payload)
            checkpoint_before_request = Checkpoint.objects.filter(user=self.user, date=date).first()

            factory = APIRequestFactory()
            payload = {'is_editable': False}
            request = factory.patch(url, payload, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"patch": "update_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(response.data.get('checkpoint'))
            self.assertFalse(response.data['checkpoint']['is_editable'])

            checkpoint_after_request = Checkpoint.objects.filter(user=self.user, date=date).first()
            self.assertEqual(checkpoint_before_request.date, checkpoint_after_request.date)
            self.assertFalse(checkpoint_after_request.is_editable)
            self.assertEqual(checkpoint_before_request.measurement_point_01,
                             checkpoint_after_request.measurement_point_01)

            checkpoint_before_request.delete()

    def test_update_measurement_400_wrong_date_in_request(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#update_measurement"""

        # дано: запрашиваем обновление чекпоинта за некорректную дату
        # ожидается: ошибка 400
        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        CheckpointFactory(date=date, user=self.user, measurement_point_01=100)

        checkpoint_before_request = Checkpoint.objects.filter(user=self.user, date=date).first()
        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', '2018-04-32', self.user, None),
            ('/api/checkpoints/measurements/2018-04-16/', '2018-13-01', self.user, None),
            ('/api/checkpoints/measurements/2018-04-16/', '2018.04.16', self.user, None),
        ]
        for url, wrong_date, user, user_id in request_args:
            factory = APIRequestFactory()
            payload = {}
            request = factory.patch(url, payload, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"patch": "update_measurement"})
            response = view(request, wrong_date, user_id)

            self.assertEqual(response.status_code, 400)

            checkpoint_after_request = Checkpoint.objects.filter(user=self.user, date=date).first()
            self.assertEqual(checkpoint_before_request.date, checkpoint_after_request.date)
            self.assertEqual(checkpoint_before_request.is_editable, checkpoint_after_request.is_editable)
            self.assertEqual(checkpoint_before_request.measurement_point_01,
                             checkpoint_after_request.measurement_point_01)

    def test_update_measurement_400_wrong_date_in_payload(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#update_measurement"""

        # дано: запрашиваем обновление чекпоинта за некорректную дату
        # ожидается: ошибка 400
        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        CheckpointFactory(date=date, user=self.user, measurement_point_01=100)

        checkpoint_before_request = Checkpoint.objects.filter(user=self.user, date=date).first()
        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', '2018-04-32', self.user, None),
            ('/api/checkpoints/measurements/2018-04-16/', '2018-13-01', self.user, None),
            ('/api/checkpoints/measurements/2018-04-16/', '2018.04.16', self.user, None),
        ]
        for url, wrong_date, user, user_id in request_args:
            factory = APIRequestFactory()
            payload = {'date': wrong_date}
            request = factory.patch(url, payload, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"patch": "update_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 400)

            checkpoint_after_request = Checkpoint.objects.filter(user=self.user, date=date).first()
            self.assertEqual(checkpoint_before_request.date, checkpoint_after_request.date)
            self.assertEqual(checkpoint_before_request.is_editable, checkpoint_after_request.is_editable)
            self.assertEqual(checkpoint_before_request.measurement_point_01,
                             checkpoint_after_request.measurement_point_01)

    def test_update_measurement_400_try_to_close_not_filled_checkpoint(self):
        # дано: есть чекпоинт за запрашиваемую дату (не все замеры заполнены); делаем чекпоинт нередактируемым
        # ожидается: ошибка, так как пытаются закрыть чекпоинт с незаполненными замерами

        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
            CheckpointFactory(date=date, user=self.user, measurement_point_01=100)
            checkpoint_before_request = Checkpoint.objects.filter(user=self.user, date=date).first()

            factory = APIRequestFactory()
            payload = {'is_editable': False}
            request = factory.patch(url, payload, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"patch": "update_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 400)

            checkpoint_after_request = Checkpoint.objects.filter(user=self.user, date=date).first()
            self.assertEqual(checkpoint_before_request.date, checkpoint_after_request.date)
            self.assertEqual(checkpoint_before_request.is_editable, checkpoint_after_request.is_editable)

            checkpoint_before_request.delete()

    def test_update_measurement_403(self):
        """Tests for successful bad in srbc.views.api.v1.diary.CheckPointMeasurementSet#update_measurement"""

        # дано: обычный пользователь (не стафф) пытается обновить данные по чекпоинту другого пользователя
        # ожидается: ошибка 403
        another_user = UserFactory(profile__is_active=True, profile__is_in_club=False)

        # === запрос
        factory = APIRequestFactory()
        request = factory.patch('/api/checkpoints/%d/measurements/2018-04-16/' % another_user.id, format='json')
        force_authenticate(request, user=self.user)
        view = CheckPointMeasurementSet.as_view({"patch": "update_measurement"})
        response = view(request, '2018-04-16', another_user.id)

        self.assertEqual(response.status_code, 403)

    def test_update_measurement_404(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#update_measurement"""

        # дано: у пользователя есть чекпоинт за запрашиваемую дату, но он уже не редактируемый
        # ожидается: успешный ответ с обновленными данными по чекпоинту
        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        CheckpointFactory(date=date, user=self.user, measurement_point_01=100, is_editable=False)

        checkpoint_before_request = Checkpoint.objects.filter(user=self.user, date=date).first()
        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            payloads = [
                {'measurement_point_01': 90},
                {'date': '2018-04-17'},
                {'is_editable': True},
            ]
            for payload in payloads:
                factory = APIRequestFactory()
                request = factory.patch(url, payload, format='json')
                force_authenticate(request, user=user)
                view = CheckPointMeasurementSet.as_view({"patch": "update_measurement"})
                response = view(request, '2018-04-16', user_id)

                self.assertEqual(response.status_code, 404)

                checkpoint_after_request = Checkpoint.objects.filter(user=self.user, date=date).first()
                self.assertEqual(checkpoint_before_request.measurement_point_01,
                                 checkpoint_after_request.measurement_point_01)
                self.assertEqual(checkpoint_before_request.is_editable, checkpoint_after_request.is_editable)
                self.assertEqual(checkpoint_before_request.date, checkpoint_after_request.date)

    def test_update_measurement_409(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#update_measurement"""

        # дано: у пользователя есть чекпоинт за запрашиваемую дату;
        #       меняем дату чекпоинта на дату, для которой уже есть чекпоинт
        # ожидается: ошибка 409
        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        another_date = datetime.datetime.strptime('2018-04-17', '%Y-%m-%d').date()
        CheckpointFactory(date=date, user=self.user, measurement_point_01=100)
        CheckpointFactory(date=another_date, user=self.user, measurement_point_01=100)

        checkpoint_before_request = Checkpoint.objects.filter(user=self.user, date=date).first()
        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            factory = APIRequestFactory()
            payload = {'date': '2018-04-17'}
            request = factory.patch(url, payload, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"patch": "update_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 409)

            checkpoint_after_request = Checkpoint.objects.filter(user=self.user, date=date).first()
            self.assertEqual(checkpoint_before_request.date, checkpoint_after_request.date)
            self.assertEqual(checkpoint_before_request.is_editable, checkpoint_after_request.is_editable)
            self.assertEqual(checkpoint_before_request.measurement_point_01,
                             checkpoint_after_request.measurement_point_01)

    def test_delete_measurement_204(self):
        """Tests for successful response in srbc.views.api.v1.diary.CheckPointMeasurementSet#delete_measurement"""

        # дано: пользователь удаляет РЕДАКТИРУЕМЫЙ чекпоинт за дату
        # ожидается: удаление одного чекпоинта, успешный ответ (код 204)

        another_date = datetime.datetime.strptime('2018-04-17', '%Y-%m-%d').date()
        another_checkpoint = CheckpointFactory(date=another_date, user=self.user)

        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
            CheckpointFactory(date=date, user=self.user)

            factory = APIRequestFactory()
            request = factory.delete(url, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"delete": "delete_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 204)
            self.assertEqual(list(Checkpoint.objects.filter(user=self.user)), [another_checkpoint])

    def test_delete_measurement_400(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#delete_measurement"""

        # дано: запрашиваем удаление чекпоинта за некорректную дату
        # ожидается: ошибка 400
        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        CheckpointFactory(date=date, user=self.user, measurement_point_01=100)

        checkpoint_before_request = Checkpoint.objects.filter(user=self.user, date=date).first()
        # === запрос
        bad_dates = [
            '2018-04-32',
            '2018-13-01',
            '2018.04.16',
            '01-01-2018',
        ]
        for bad_date in bad_dates:
            factory = APIRequestFactory()
            request = factory.delete('/api/checkpoints/measurements/%s/' % bad_date, format='json')
            force_authenticate(request, user=self.user)
            view = CheckPointMeasurementSet.as_view({"delete": "delete_measurement"})
            response = view(request, bad_date)

            self.assertEqual(response.status_code, 400)
            self.assertEqual(list(Checkpoint.objects.filter(user=self.user)), [checkpoint_before_request])

    def test_delete_measurement_403(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#delete_measurement"""

        # дано: обычный пользователь (не стафф) пытается удалить чекпоинт другого пользователя
        # ожидается: ошибка 403
        another_user = UserFactory(profile__is_active=True, profile__is_in_club=False)
        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        checkpoint_before_request = CheckpointFactory(date=date, user=another_user)

        # === запрос
        factory = APIRequestFactory()
        request = factory.delete('/api/checkpoints/%d/measurements/2018-04-16/' % another_user.id, format='json')
        force_authenticate(request, user=self.user)
        view = CheckPointMeasurementSet.as_view({"delete": "delete_measurement"})
        response = view(request, '2018-04-16', another_user.id)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(list(Checkpoint.objects.filter(user=another_user)), [checkpoint_before_request])

    def test_delete_measurement_404(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#delete_measurement"""

        # дано: пользователь удаляет НЕРЕДАКТИРУЕМЫЙ чекпоинт за дату
        # ожидается: ошибка 404

        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        checkpoint = CheckpointFactory(date=date, user=self.user, is_editable=False)

        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            factory = APIRequestFactory()
            request = factory.delete(url, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"delete": "delete_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 404)
            self.assertEqual(list(Checkpoint.objects.filter(user=self.user)), [checkpoint])

    def test_delete_measurement_404_2(self):
        """Tests for bad response in srbc.views.api.v1.diary.CheckPointMeasurementSet#delete_measurement"""

        # дано: пользователь удаляет РЕДАКТИРУЕМЫЙ чекпоинт за дату, но в чекпоинте is_measurements_done=True
        # ожидается: ошибка 404

        date = datetime.datetime.strptime('2018-04-16', '%Y-%m-%d').date()
        checkpoint = CheckpointFactory(date=date, user=self.user, is_editable=True, is_measurements_done=True)

        # === запрос
        request_args = [
            ('/api/checkpoints/measurements/2018-04-16/', self.user, None),
            ('/api/checkpoints/%d/measurements/2018-04-16/' % self.user.id, self.staff_user, self.user.id),
        ]
        for url, user, user_id in request_args:
            factory = APIRequestFactory()
            request = factory.delete(url, format='json')
            force_authenticate(request, user=user)
            view = CheckPointMeasurementSet.as_view({"delete": "delete_measurement"})
            response = view(request, '2018-04-16', user_id)

            self.assertEqual(response.status_code, 404)
            self.assertEqual(list(Checkpoint.objects.filter(user=self.user)), [checkpoint])

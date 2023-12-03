# -*- coding: utf-8 -*-
import datetime

from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from srbc.models import ParticipationGoal
from srbc.tests.factories import UserFactory, ParticipationGoalFactory
from srbc.views.api.v1.diary import ParticipationGoalSet

# FIXME - тоже потом переделать
# тут и ниже все что связано с profile.is_active и profile__wave


class ParticipationGoalTest(TestCase):
    def setUp(self):
        self.user = UserFactory(profile__is_active=True, profile__is_in_club=False,
                                profile__wave__start_date=datetime.date(2018, 1, 1))
        self.staff_user = UserFactory(is_staff=True)

    def test_edit_goal_400_no_text(self):
        """ Test logic for srbc.views.api.v1.diary.ParticipationGoalSet#edit_goal """

        # дано: в запросе на редактирование не передали текста
        # ожидается: ошибка запроса

        participant_goal = ParticipationGoalFactory(user=self.user)

        # === запрос
        url = 'api/goals/%s' % participant_goal.id
        factory = APIRequestFactory()
        request = factory.post(url, format='json')
        force_authenticate(request, user=self.user)
        view = ParticipationGoalSet.as_view({"post": "edit_goal"})
        response = view(request, str(participant_goal.id))

        self.assertEqual(response.status_code, 400)

    def test_edit_goal_400_bad_text(self):
        """ Test logic for srbc.views.api.v1.diary.ParticipationGoalSet#edit_goal """

        # дано: в запросе на редактирование передали текст, но в неверном формате (ожидается строка)
        # ожидается: ошибка запроса

        participant_goal = ParticipationGoalFactory(user=self.user)

        bad_texts = [123, None, 15.0, ['foo', 'bar']]

        # === запрос
        url = 'api/goals/%s' % participant_goal.id
        factory = APIRequestFactory()
        for text in bad_texts:
            payload = {'text': text}
            request = factory.post(url, payload, format='json')
            force_authenticate(request, user=self.user)
            view = ParticipationGoalSet.as_view({"post": "edit_goal"})
            response = view(request, str(participant_goal.id))

            self.assertEqual(response.status_code, 400)

    def test_edit_goal_400_bad_goal_id(self):
        """ Test logic for srbc.views.api.v1.diary.ParticipationGoalSet#edit_goal """

        # дано: в запросе на редактирование передали несуществующий id цели
        # ожидается: ошибка запроса
        goal_id = 12345

        # === запрос
        url = 'api/goals/%s' % goal_id
        factory = APIRequestFactory()
        request = factory.post(url, data={'text': 'foobar'}, format='json')
        force_authenticate(request, user=self.user)
        view = ParticipationGoalSet.as_view({"post": "edit_goal"})
        response = view(request, str(goal_id))

        self.assertEqual(response.status_code, 400)

        # дано: в запросе на редактирование передали id НЕРЕДАКТИРУЕМОЙ цели
        participant_goal_1 = ParticipationGoalFactory(user=self.user, status='REACHED')
        participant_goal_2 = ParticipationGoalFactory(user=self.user, status='DELETED')

        for participant_goal in (participant_goal_1, participant_goal_2):
            # === запрос
            url = 'api/goals/%s' % participant_goal.id
            factory = APIRequestFactory()
            request = factory.post(url, data={'text': 'foobar'}, format='json')
            force_authenticate(request, user=self.user)
            view = ParticipationGoalSet.as_view({"post": "edit_goal"})
            response = view(request, str(participant_goal.id))

            self.assertEqual(response.status_code, 400)

    def test_edit_goal_ok(self):
        """ Test logic for srbc.views.api.v1.diary.ParticipationGoalSet#edit_goal """

        # дано: изменяем текст цели
        # ожидается: старая цель отмечатся как удаленная, создается новая цель с новым текстом
        participant_goal = ParticipationGoalFactory(user=self.user, text='foobar', ordernum=99)

        self.assertEqual(len(ParticipationGoal.objects.all()), 1)

        # === запрос
        url = 'api/goals/%s' % participant_goal.id
        factory = APIRequestFactory()
        request = factory.post(url, data={'text': 'foobar EDITED'}, format='json')
        force_authenticate(request, user=self.user)
        view = ParticipationGoalSet.as_view({"post": "edit_goal"})
        response = view(request, str(participant_goal.id))

        goals = ParticipationGoal.objects.all()
        old_goal = goals[0] if goals[0].id == participant_goal.id else goals[1]
        new_goal = goals[1] if goals[0].id == participant_goal.id else goals[0]

        self.assertEqual(response.status_code, 204)
        self.assertEqual(len(goals), 2)

        # проверим статусы
        self.assertEqual(old_goal.status, 'DELETED')
        self.assertEqual(new_goal.status, 'NEW')
        # проверим, что текст у старого не изменился
        self.assertEqual(old_goal.text, 'foobar')
        self.assertEqual(new_goal.text, 'foobar EDITED')
        # проверим, что порядок сохранился
        self.assertEqual(old_goal.ordernum, new_goal.ordernum)

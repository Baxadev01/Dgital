# -*- coding: utf-8 -*-

from django.test import TestCase

from srbc.social import get_ig_user_data

PUBLIC_ACCOUNT = 'damedvedev'
PRIVATE_ACCOUNT = 'unit_test'
NOT_EXISTING_ACCOUNT = 'foobar_a_b_132352323237'


class TestSocialUtils(TestCase):
    """
        Мини-тест. Запрос к инстаграмму не мокаем.
        Пока юнит-тесты вручную гоняются, а не на битбакете, то так можно оставить.
        Плюс, пока нет sentry, то более-менее вовремя узнаем, если что изменилось в Instagram-е.
    """

    def test_private_account(self):
        user_data = get_ig_user_data(username=PRIVATE_ACCOUNT)
        self.assertTrue(isinstance(user_data, dict))
        self.assertTrue('is_private' in user_data)
        self.assertEqual(user_data['is_private'], True)

    def test_public_account(self):
        user_data = get_ig_user_data(username=PUBLIC_ACCOUNT)
        self.assertTrue(isinstance(user_data, dict))
        self.assertTrue('is_private' in user_data)
        self.assertEqual(user_data['is_private'], False)

    def test_not_existing_account(self):
        user_data = get_ig_user_data(username=NOT_EXISTING_ACCOUNT)
        self.assertEqual(user_data, None)

# -*- coding: utf-8 -*-

from django.test import TestCase

from srbc.forms import UsernameForm
from .factories import UserFactory


class TestUsernameForm(TestCase):
    """ Тесты валидации юзернейма для srbc.forms.UsernameForm     
    """
    def setUp(self):
        self.user = UserFactory()

    def test_valid_usernames(self):
        valid_usernames = [
            'test1',
            'test123456789012',
            'test_1',
            'test.1',
            'a_test1',
            'a.test1',
            'test1_a',
            'test1.a',
            'test1_a.b',
            'a12test',
            '12test',
        ]
        for username in valid_usernames:
            form = UsernameForm({'username': username}, user=self.user)
            self.assertTrue(form.is_valid())

    def test_invalid_usernames(self):
        invalid_usernames = [
            'тест1',
            'test',
            'test1234567890123',
            'test_.1',
            '_test1',
            '.test1',
            'test1_',
            'test1.',
            'test1_',
            'test1.',
            'test1._a',
            'test1_.a',
            'test1..a',
            'test1__a',
            '?asfasf',
            'test1?asfasf',
            'test1>asf',
            'test1ыа',
        ]
        for username in invalid_usernames:
            form = UsernameForm({'username': username}, user=self.user)
            self.assertFalse(form.is_valid())
            print((form.errors['username'][0]))
            self.assertEqual(form.errors['username'][0], UsernameForm._regex_error_msg)

import logging
from http import HTTPStatus

from captcha.models import CaptchaStore
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

logger = logging.getLogger(__name__)


class RegisterUserTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Создаём капчу один раз для всех тестов
        cls.captcha = CaptchaStore.objects.create(
            challenge='dummy-challenge',
            response='dummy-response',
        )

    def test_form_registration_get(self):
        path = reverse('users:register')
        response = self.client.get(path)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'users/register.html')
        logger.info("Проверка получения формы регистрации пользователя прошла успешно")

    def test_user_registration_success(self):
        data = {
            'username': 'test',
            'email': 'a@a.ru',
            'first_name': 'test',
            'last_name': 'test',
            'password1': '12345QPow!',
            'password2': '12345QPow!',
            'captcha_0': self.captcha.hashkey,
            'captcha_1': self.captcha.response,
        }
        user_model = get_user_model()
        path = reverse('users:register')

        # Отправляем форму
        response = self.client.post(path, data)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertTrue(user_model.objects.filter(username='test').exists())
        logger.info("Проверка регистрации пользователя с корректными данными прошла успешно")

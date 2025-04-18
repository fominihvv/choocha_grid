import logging
from http import HTTPStatus

from captcha.models import CaptchaStore
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

logger = logging.getLogger(__name__)


class RegisterUserTestCase(TestCase):
    def setUp(self):
        # Создаём капчу один раз для всех тестов
        self.captcha = CaptchaStore.objects.create(
            challenge='dummy-challenge',
            response='dummy-response',
        )

        self.data = {
            'username': 'test',
            'email': 'test@test.ru',
            'first_name': 'test',
            'last_name': 'test',
            'password1': '12345QPow!',
            'password2': '12345QPow!',
            'captcha_0': self.captcha.hashkey,
            'captcha_1': self.captcha.response,
        }

    def test_form_registration_get(self):
        path = reverse('users:register')
        response = self.client.get(path)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'users/register.html')
        logger.info("Проверка получения формы регистрации пользователя прошла успешно")

    def test_user_registration_success(self):
        user_model = get_user_model()
        path = reverse('users:register')

        # Отправляем форму
        response = self.client.post(path, self.data)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, reverse('users:login'))
        self.assertTrue(user_model.objects.filter(username=self.data['username']).exists())
        logger.info("Проверка регистрации пользователя с корректными данными прошла успешно")

    def test_user_registration_password_mismatch(self):
        path = reverse('users:register')
        self.data['password2'] = '12345QPow!A'

        # Отправляем форму
        response = self.client.post(path, self.data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Введенные пароли не совпадают')
        logger.info("Проверка регистрации пользователя с разными паролями прошла успешно")

    def test_user_registration_username_exists(self):
        user_model = get_user_model()
        user_model.objects.create_user(username=self.data['username'])
        path = reverse('users:register')

        # Отправляем форму
        response = self.client.post(path, self.data)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, 'Пользователь с таким именем уже существует')
        logger.info("Проверка регистрации пользователя с существующим именем прошла успешно")

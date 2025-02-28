import logging
from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from notes.models import Note

logger = logging.getLogger(__name__)


class GetPagesTestCase(TestCase):
    fixtures = ['test_bd.json']

    def setUp(self):
        """ Инициализация перед каждым тестом """
        # cache.cache.clear()

    def test_01_mainpage(self):
        path = reverse('home')
        response = self.client.get(path)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'notes/index.html')
        self.assertEqual(response.context_data['title'], 'Главная страница')
        # print("Проверка главной страницы прошла успешно")
        logger.info("Проверка главной страницы прошла успешно")  # логирование в зависимости от настроек в settings.py

    def test_02_redirect_addpage(self):
        path = reverse('add_post')
        redirect_uri = '/users/login/?next=' + path
        response = self.client.get(path)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, redirect_uri)
        # print("Проверка редиректа на страницу добавления поста прошла успешно")
        logger.info("Проверка редиректа на страницу добавления поста прошла успешно")

    def test_03_not_found_page(self):
        path = "/not_found_page"
        response = self.client.get(path)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # print("Проверка несуществующей страницы прошла успешно")
        logger.info("Проверка несуществующей страницы прошла успешно")

    def test_04_data_mainpage(self):
        path = reverse('home')
        response = self.client.get(path)
        notes_lst = Note.published.all().select_related('cat')
        self.assertQuerySetEqual(response.context_data['posts'], notes_lst[:5])
        # print("Проверка данных главной страницы прошла успешно")
        logger.info("Проверка данных главной страницы прошла успешно")

    def test_05_paginate_mainpage(self):
        path = reverse('home')
        page = 2
        pagination_by = 5
        response = self.client.get(path + f'?page={page}')
        notes_lst = Note.published.all().select_related('cat')
        self.assertQuerySetEqual(response.context_data['posts'],
                                 notes_lst[(page - 1) * pagination_by:page * pagination_by])
        # print("Проверка разбивки постраничной навигации главной страницы прошла успешно")
        logger.info("Проверка разбивки постраничной навигации главной страницы прошла успешно")

    def test_06_content_post(self):
        notes_post = Note.published.get(pk=1)
        path = reverse('post', args=[notes_post.slug])
        response = self.client.get(path)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context_data['post'].content_full, notes_post.content_full)
        # print("Проверка содержимого поста прошла успешно")
        logger.info("Проверка содержимого поста прошла успешно")

    def tearDown(self):
        """ Действия после выполнения каждого теста """

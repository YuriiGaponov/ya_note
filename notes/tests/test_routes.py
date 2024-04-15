from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.another_user = User.objects.create(username='Другой пользователь')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.user
        )
        cls.notes_list = Note.objects.filter(author=cls.user)
        cls.SLUG = {'slug': cls.note.slug}

    def test_pages_availability(self):
        """
        Доступность домашней страницы,
        страниц входа/выхода/регистрации.
        """
        urls = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        )
        for name in urls:
            with self.subTest(name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    'Страница недоступна.'
                )

    def test_create_note_page(self):
        """Создание записи."""
        self.client.force_login(self.user)
        Note.objects.create(
            title='Заголовок1',
            text='Текст1',
            author=self.user
        )
        self.assertEqual(Note.objects.count(), 2,
                         'Новая запись не создается')

    def test_note_detail_edit_delete_pages_availability(self):
        """
        Доступность страницы просмотра, удаления, редактирования записи
        другому пользователю
        """
        users_statuses = (
            (self.user, HTTPStatus.OK),
            (self.another_user, HTTPStatus.NOT_FOUND),
        )
        urls = (
            ('notes:detail', self.SLUG),
            ('notes:edit', self.SLUG),
            ('notes:delete', self.SLUG),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name, kwargs in urls:
                with self.subTest(user=user, status=status,
                                  name=name, kwargs=kwargs):
                    url = reverse(name, kwargs=kwargs)
                    response = self.client.get(url)
                    self.assertEqual(
                        response.status_code, status,
                        ('Другой пользователь может'
                         'просматривать, изменять и удалять записи.')
                        )

    def test_note_list_success_page_availability(self):
        """
        Доступность страниц списка, подтверждения успешного создания записей.
        """
        urls = ('notes:list', 'notes:success',)
        for name in urls:
            url = reverse(name)
            self.client.force_login(self.user)
            response = self.client.get(url)
            with self.subTest(url=url, response=response.status_code):
                self.assertEqual(response.status_code, HTTPStatus.OK,
                                 'Страница списка записей недоступна.')

    def test_1redirect_edit_detail_delete_for_anonymous_client(self):
        """Переадресация страниц для анонимного пользователя."""
        login_url = reverse('users:login')
        urls = (
            ('notes:detail', self.SLUG),
            ('notes:edit', self.SLUG),
            ('notes:delete', self.SLUG),
            ('notes:add', None),
            ('notes:list', None),
            ('notes:success', None)
        )
        for name, kwargs in urls:
            with self.subTest(name=name):
                url = reverse(name, kwargs=kwargs)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url,)

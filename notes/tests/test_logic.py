from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.models import Note

User = get_user_model()


class TestEditDeleteNote(TestCase):

    NOTE_TEXT = 'Текст'
    NEW_NOTE_TEXT = 'Измененный текст'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Пользователь')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title='Заголовок',
            text=cls.NOTE_TEXT,
            slug='slug',
            author=cls.author
        )
        cls.reader = User.objects.create(username='Другой пользователь')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        kwargs = {'slug': cls.note.slug}
        cls.add_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', kwargs=kwargs)
        cls.delete_url = reverse('notes:delete', kwargs=kwargs)
        cls.form_data = {
            'title': cls.note.title,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.note.slug
        }
        cls.new_note_form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new_slug'
        }

    def test_user_can_create_note_page(self):
        """Авторизованный пользователь может создать заметку."""
        response = self.author_client.post(
            self.add_url, data=self.new_note_form_data
        )
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 2, 'Новая запись не создается')
        new_note = Note.objects.get(slug=self.new_note_form_data['slug'])
        self.assertEqual(new_note.title, self.new_note_form_data['title'])
        self.assertEqual(new_note.text, self.new_note_form_data['text'])
        self.assertEqual(new_note.slug, self.new_note_form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note_page(self):
        """Анонимный пользователь не может создать заметку."""
        response = self.client.post(self.add_url, data=self.new_note_form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.add_url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 1)

    def test_author_can_edit_note(self):
        """Автор может изменить заметку."""
        self.author_client.post(self.edit_url, data=self.form_data)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT,
                         'Автор не может изменить свою заметку.')

    def test_author_can_delete_note(self):
        """Автор может удалить запись."""
        self.author_client.delete(self.delete_url)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 0,
                         'Автор не может удалить свою заметку.')

    def test_reader_cant_edit_note(self):
        """Другой пользователь не может изменить заметку."""
        self.reader_client.post(self.edit_url, data=self.form_data)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT,
                         'Пользователь может изменить чужую заметку.')

    def test_reader_cant_delete_note(self):
        """Другой пользователь не может удалить заметку."""
        self.reader_client.delete(self.edit_url)
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1,
                         'Пользователь может удалить чужую заметку.')


class TestCreateNote(TestCase):

    UNIQUE_SLUG_ERROR = 'slug должен быть уникальным для каждой заметки.'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='slug',
            author=cls.user
        )
        cls.another_user = User.objects.create(username='Другой пользователь')
        cls.another_user_client = Client()
        cls.another_user_client.force_login(cls.another_user)
        cls.add_url = reverse('notes:add')
        cls.form_data = {
            'title': 'Другой заголовок',
            'text': 'Другой текст',
            'slug': cls.note.slug
        }
        cls.empty_slug_form_data = {
            'title': 'Другой заголовок',
            'text': 'Другой текст',
            'slug': ''
        }

    def test_user_cant_create_several_notes_one_slug(self):
        """Нельзя создать несколько заметок с одинаковым slug."""
        self.user_client.post(self.add_url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1, self.UNIQUE_SLUG_ERROR)

    def test_another_user_cant_create_several_notes_one_slug(self):
        """
        Нельзя создать заметку со slug,
        использованным другим пользователем.
        """
        self.another_user_client.post(self.add_url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1, self.UNIQUE_SLUG_ERROR)

    def test_create_note_empty_slug(self):
        """Формирование slug, если он не заполнен."""
        self.user_client.post(self.add_url, data=self.empty_slug_form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 2, self.UNIQUE_SLUG_ERROR)
        new_note = Note.objects.get(pk=2)
        self.assertEqual(
            new_note.slug, slugify(self.empty_slug_form_data['title'])
        )

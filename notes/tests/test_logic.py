from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

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
        cls.edit_url = reverse('notes:edit', kwargs=kwargs)
        cls.delete_url = reverse('notes:delete', kwargs=kwargs)
        cls.form_data = {
            'title': cls.note.title,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.note.slug
        }

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

    def test_reader_cant_dit_note(self):
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

    def test_user_cant_create_several_notes_one_slug(self):
        """Нельзя создать несколько заметок с одинаковым slug."""
        self.user_client.post(self.add_url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1,
                         'slug должен быть уникальным для каждой заметки.')

    def test_another_user_cant_create_several_notes_one_slug(self):
        """Нельзя создать несколько заметок с одинаковым slug."""
        self.another_user_client.post(self.add_url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1,
                         'slug должен быть уникальным для каждой заметки.')

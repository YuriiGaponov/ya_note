from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import NoteForm

User = get_user_model()


class TestNoteList(TestCase):

    LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        all_notes = [
            Note(
                title=f'Заголовок {index}',
                text=f'Текст {index}',
                slug=f'slug{index}',
                author=cls.author
                 ) for index in range(10)
         ]
        Note.objects.bulk_create(all_notes)

    def test_order_notes(self):
        """Порядок вывода записей."""
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        object_list = response.context['object_list']
        all_notes = [note.pk for note in object_list]
        sorted_notes = sorted(all_notes)
        self.assertEqual(sorted_notes, all_notes,
                         'Список записей выводится неправильно.')


class TestNoteAddEdit(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.author = User.objects.create(username='Автор')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            slug='slug',
            author=cls.author
        )
        kwargs = {'slug': cls.note.slug}
        cls.urls = (
            ('notes:add', None),
            ('notes:edit', kwargs)
        )

    def test_authorized_client_has_form(self):
        """Наличие объекта формы в контексте."""
        self.client.force_login(self.author)
        for name, kwargs in self.urls:
            url = reverse(name, kwargs=kwargs)
            response = self.client.get(url)
            self.assertIn('form', response.context,
                          'Объект форме не передается в контекст.')
            self.assertIsInstance(response.context['form'], NoteForm,
                                  'Не передается нужный объект формы.')

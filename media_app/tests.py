"""Тесты автомодерации комментариев."""

from django.test import SimpleTestCase

from media_app.forms import CommentForm
from media_app.moderation import contains_stop_words, find_stop_words


class CommentModerationTests(SimpleTestCase):
    """Проверка стоп-слов и формы комментария."""

    def test_find_stop_words_detects_forbidden_word(self):
        self.assertEqual(find_stop_words('Это просто spam в тексте'), ['spam'])

    def test_find_stop_words_ignores_clean_text(self):
        self.assertEqual(find_stop_words('Отличный кавер, молодцы!'), [])

    def test_contains_stop_words(self):
        self.assertTrue(contains_stop_words('Здесь есть casino'))
        self.assertFalse(contains_stop_words('Классное выступление'))

    def test_comment_form_rejects_stop_words(self):
        form = CommentForm(data={'text': 'Купите реклама у меня', 'is_anonymous': False})
        self.assertFalse(form.is_valid())
        self.assertIn('text', form.errors)

    def test_comment_form_accepts_clean_comment(self):
        form = CommentForm(data={'text': 'Очень крутой кавер!', 'is_anonymous': False})
        self.assertTrue(form.is_valid())

"""Автомодерация комментариев: проверка на стоп-слова."""

import re

from django.conf import settings

DEFAULT_STOP_WORDS = {
    'spam',
    'scam',
    'xxx',
    'porn',
    'порно',
    'спам',
    'мошенник',
    'мошенничество',
    'реклама',
    'casino',
    'казино',
    'наркотик',
    'наркота',
    'сука',
    'блять',
    'блядь',
    'хуй',
    'пизда',
    'ебать',
    'fuck',
    'shit',
    'bitch',
}


def get_stop_words():
    """Возвращает набор стоп-слов из настроек или значения по умолчанию."""
    configured = getattr(settings, 'COMMENT_STOP_WORDS', None)
    if configured is None:
        return DEFAULT_STOP_WORDS
    return {word.lower().strip() for word in configured if word.strip()}


def find_stop_words(text):
    """Находит стоп-слова в тексте комментария.

    Args:
        text: Текст комментария.

    Returns:
        list[str]: Список найденных запрещённых слов.
    """
    if not text:
        return []

    normalized = text.lower()
    found = []

    for word in get_stop_words():
        pattern = rf'(?<!\w){re.escape(word)}(?!\w)'
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            found.append(word)

    return sorted(set(found))


def contains_stop_words(text):
    """True, если текст содержит хотя бы одно стоп-слово."""
    return bool(find_stop_words(text))

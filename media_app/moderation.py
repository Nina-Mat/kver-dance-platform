"""Автомодерация пользовательского контента: проверка на стоп-слова."""

import json
import re

from django.conf import settings

MODERATION_POLICY_MESSAGE = (
    'Нарушение политики платформы в связи с попыткой использования нецензурной лексики.'
)

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
    'суки',
    'сучка',
    'сучара',
    'блять',
    'блядь',
    'бля',
    'блят',
    'хуй',
    'хуйня',
    'хуесос',
    'хуило',
    'хуев',
    'пизда',
    'пиздец',
    'пизд',
    'ебать',
    'ебал',
    'ебан',
    'ебло',
    'ёб',
    'йоб',
    'йобан',
    'мудак',
    'мудила',
    'гандон',
    'шлюха',
    'дебил',
    'fuck',
    'shit',
    'bitch',
}


def get_stop_words():
    """Возвращает набор стоп-слов из настроек или значения по умолчанию."""
    configured = getattr(settings, 'CONTENT_STOP_WORDS', None)
    if configured is None:
        configured = getattr(settings, 'COMMENT_STOP_WORDS', None)
    if configured is None:
        return DEFAULT_STOP_WORDS
    return {word.lower().strip() for word in configured if word.strip()}


def get_stop_words_list():
    """Список стоп-слов для клиентской проверки (JSON)."""
    return sorted(get_stop_words())


def get_stop_words_json():
    """JSON-массив стоп-слов для шаблонов."""
    return json.dumps(get_stop_words_list(), ensure_ascii=False)


def find_stop_words(text):
    """Находит стоп-слова в тексте."""
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

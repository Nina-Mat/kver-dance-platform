"""Утилиты модуля events: загрузка файлов и конфигурация форм заявок."""

import uuid
from pathlib import Path

from django.utils.text import slugify


ALLOWED_AUDIO_TYPES = (
    'audio/mpeg',
    'audio/mp3',
    'audio/wav',
    'audio/x-wav',
    'audio/wave',
)
ALLOWED_AUDIO_EXTENSIONS = ('.mp3', '.wav')
MAX_AUDIO_SIZE = 50 * 1024 * 1024


def application_audio_upload_to(instance, filename):
    """Сохраняет аудиофайл заявки в applications/ с уникальным хешем."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        ext = '.mp3'
    return f'applications/{uuid.uuid4().hex}{ext}'


def validate_audio_file(audio_file):
    """Проверяет MIME-тип, расширение и размер аудиофайла.

    Args:
        audio_file: Загруженный файл Django.

    Returns:
        UploadedFile: Проверенный файл.

    Raises:
        ValidationError: Если файл не проходит проверку.
    """
    from django.core.exceptions import ValidationError

    if not audio_file:
        return audio_file

    ext = Path(audio_file.name).suffix.lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValidationError('Допустимы только файлы MP3 и WAV.')

    content_type = getattr(audio_file, 'content_type', '')
    if content_type and content_type not in ALLOWED_AUDIO_TYPES:
        raise ValidationError('Допустимы только аудиофайлы MP3 и WAV.')

    if audio_file.size > MAX_AUDIO_SIZE:
        raise ValidationError('Размер аудиофайла не должен превышать 50 МБ.')

    return audio_file


def build_form_fields_config(field_formset, require_audio):
    """Собирает JSON-конфиг полей формы заявки из formset.

    Args:
        field_formset: Валидный formset кастомных полей.
        require_audio: Требуется ли загрузка аудиотрека.

    Returns:
        dict: Конфигурация для Event.form_fields.
    """
    fields = []
    used_names = set()

    for index, form in enumerate(field_formset):
        if not form.cleaned_data or form.cleaned_data.get('DELETE'):
            continue

        label = form.cleaned_data.get('label', '').strip()
        if not label:
            continue

        base_name = slugify(label) or f'field_{index}'
        name = base_name
        suffix = 1
        while name in used_names:
            name = f'{base_name}_{suffix}'
            suffix += 1
        used_names.add(name)

        fields.append({
            'name': name,
            'label': label,
            'type': form.cleaned_data['field_type'],
            'required': form.cleaned_data.get('required', False),
        })

    return {
        'require_audio': require_audio,
        'fields': fields,
    }

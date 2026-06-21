from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import CoverMedia, Comment
from .moderation import find_stop_words
from .utils import parse_youtube_url, validate_video_file

BOOTSTRAP_TEXT = {'class': 'form-control'}
BOOTSTRAP_TEXTAREA = {'class': 'form-control', 'rows': 3}
BOOTSTRAP_FILE = {'class': 'form-control'}
BOOTSTRAP_CHECKBOX = {'class': 'form-check-input'}


class CoverMediaForm(forms.ModelForm):
    """Форма публикации: YouTube-ссылка или локальный видеофайл."""

    youtube_url = forms.URLField(
        label='Ссылка на YouTube',
        required=False,
        widget=forms.URLInput(attrs={
            **BOOTSTRAP_TEXT,
            'placeholder': 'https://www.youtube.com/watch?v=...',
            'id': 'id_youtube_url',
        }),
    )

    class Meta:
        model = CoverMedia
        fields = [
            'source_type',
            'title',
            'description',
            'video_file',
            'cover_image',
            'tags',
            'team',
        ]
        widgets = {
            'source_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'title': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'Название публикации',
                'id': 'id_title',
            }),
            'description': forms.Textarea(attrs={
                **BOOTSTRAP_TEXTAREA,
                'placeholder': 'Описание. Используйте @username для упоминаний.',
                'id': 'id_description',
            }),
            'video_file': forms.FileInput(attrs={
                **BOOTSTRAP_FILE,
                'accept': 'video/mp4,video/webm,video/quicktime,.mp4,.webm,.mov',
                'id': 'id_video_file',
            }),
            'cover_image': forms.FileInput(attrs={
                **BOOTSTRAP_FILE,
                'accept': 'image/*',
            }),
            'tags': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'kpop, hip-hop, @username',
            }),
            'team': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'source_type': 'Тип публикации',
            'title': 'Название',
            'description': 'Описание',
            'video_file': 'Видеофайл',
            'cover_image': 'Обложка (опционально)',
            'tags': 'Теги',
            'team': 'Команда (необязательно)',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.add_input(Submit('submit', 'Опубликовать', css_class='btn-neon w-100'))

        if user:
            from accounts.models import Team
            self.fields['team'].queryset = Team.objects.filter(
                team_memberships__user=user,
            ).distinct()
        else:
            self.fields['team'].queryset = self.fields['team'].queryset.none()

    def clean(self):
        cleaned_data = super().clean()
        source_type = cleaned_data.get('source_type', 'upload')

        if source_type == 'youtube':
            youtube_url = cleaned_data.get('youtube_url') or self.data.get('youtube_url')
            if not youtube_url:
                raise forms.ValidationError('Вставьте ссылку на YouTube.')

            video_id = parse_youtube_url(youtube_url)
            if not video_id:
                raise forms.ValidationError('Неверная ссылка на YouTube.')

            cleaned_data['youtube_id'] = video_id
            cleaned_data['youtube_url'] = youtube_url

        elif source_type == 'upload':
            video_file = cleaned_data.get('video_file')
            if not video_file:
                raise forms.ValidationError('Загрузите видеофайл.')
            validate_video_file(video_file)
            cleaned_data['youtube_id'] = ''
            cleaned_data['youtube_url'] = ''

        return cleaned_data

    def clean_video_file(self):
        video_file = self.cleaned_data.get('video_file')
        if video_file:
            validate_video_file(video_file)
        return video_file


class CommentForm(forms.ModelForm):
    """Форма добавления комментария с автомодерацией текста."""

    class Meta:
        model = Comment
        fields = ['text', 'is_anonymous']
        widgets = {
            'text': forms.Textarea(attrs={
                **BOOTSTRAP_TEXTAREA,
                'placeholder': 'Напишите комментарий...',
            }),
            'is_anonymous': forms.CheckboxInput(attrs=BOOTSTRAP_CHECKBOX),
        }
        labels = {
            'text': 'Комментарий',
            'is_anonymous': 'Опубликовать анонимно',
        }

    def clean_text(self):
        """Проверяет комментарий на наличие стоп-слов."""
        text = self.cleaned_data.get('text', '').strip()
        if not text:
            raise ValidationError('Комментарий не может быть пустым.')

        forbidden_words = find_stop_words(text)
        if forbidden_words:
            raise ValidationError(
                'Комментарий содержит запрещённые слова. '
                'Исправьте текст и попробуйте снова.'
            )

        return text
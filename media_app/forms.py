from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import CoverMedia, Comment
from .moderation import find_stop_words, MODERATION_POLICY_MESSAGE
from .utils import parse_youtube_url, validate_video_file, fetch_youtube_metadata

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
            'feed_type',
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
            'feed_type': 'Показывать в ленте как',
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
            from django.db.models import Q
            self.fields['team'].queryset = Team.objects.filter(
                Q(team_memberships__user=user) | Q(leader=user),
            ).distinct()
        else:
            self.fields['team'].queryset = self.fields['team'].queryset.none()

        self.fields['feed_type'].widget = forms.HiddenInput()
        self.fields['title'].required = False

        if not self.instance.pk:
            self.fields['source_type'].initial = 'youtube'
            self.fields['feed_type'].initial = 'cover'

    def clean(self):
        cleaned_data = super().clean()
        source_type = cleaned_data.get('source_type', 'upload')

        if source_type == 'youtube':
            cleaned_data['feed_type'] = 'cover'
            youtube_url = cleaned_data.get('youtube_url') or self.data.get('youtube_url')
            if not youtube_url and self.instance.pk and self.instance.youtube_url:
                youtube_url = self.instance.youtube_url
            if not youtube_url:
                raise forms.ValidationError('Вставьте ссылку на YouTube.')

            video_id = parse_youtube_url(youtube_url)
            if not video_id:
                raise forms.ValidationError('Неверная ссылка на YouTube.')

            metadata = fetch_youtube_metadata(video_id)
            cleaned_data['youtube_id'] = video_id
            cleaned_data['youtube_url'] = youtube_url
            self.instance.youtube_id = video_id
            self.instance.youtube_url = youtube_url
            self.instance.source_type = 'youtube'

            if not (cleaned_data.get('title') or '').strip():
                cleaned_data['title'] = metadata.get('title') or f'YouTube {video_id}'
            if not (cleaned_data.get('description') or '').strip() and metadata.get('description'):
                cleaned_data['description'] = metadata['description']

        elif source_type == 'upload':
            cleaned_data['feed_type'] = 'performance'
            video_file = cleaned_data.get('video_file')
            if not video_file and not (self.instance.pk and self.instance.video_file):
                raise forms.ValidationError('Загрузите видеофайл.')
            if not (cleaned_data.get('title') or '').strip():
                raise forms.ValidationError({'title': 'Укажите название выступления.'})
            if video_file:
                validate_video_file(video_file)
            cleaned_data['youtube_id'] = ''
            cleaned_data['youtube_url'] = ''

        self._validate_profanity(cleaned_data)

        return cleaned_data

    def _validate_profanity(self, cleaned_data):
        for field_name in ('title', 'description', 'tags'):
            text = cleaned_data.get(field_name) or ''
            if find_stop_words(str(text)):
                raise ValidationError(MODERATION_POLICY_MESSAGE)

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
                'placeholder': 'Ваш комментарий...',
                'rows': 1,
                'class': 'form-control comment-compose__input',
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                **BOOTSTRAP_CHECKBOX,
                'class': 'form-check-input comment-compose__anon',
            }),
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
            raise ValidationError(MODERATION_POLICY_MESSAGE)

        return text
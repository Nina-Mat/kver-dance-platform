import re

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.forms import formset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from .models import (
    CustomUser,
    UserProfile,
    Team,
    TeamMember,
    OrganizerProfile,
    SpecialistProfile,
    PhotoCard,
    PhotoAlbum,
)
from events.models import Event
from media_app.models import CoverMedia


NICKNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_]{3,30}$')
PHONE_DIGITS_PATTERN = re.compile(r'\D')


# ========================================
# 🔐 РЕГИСТРАЦИЯ И ВХОД
# ========================================

class CustomUserCreationForm(UserCreationForm):
    """Форма регистрации с русскими подписями."""

    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'user_type', 'city', 'password1', 'password2')
        widgets = {
            'user_type': forms.RadioSelect(),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Москва'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Создать аккаунт', css_class='btn-neon w-100'))

        self.fields['username'].label = "Имя пользователя"
        self.fields['email'].label = "Email"
        self.fields['user_type'].label = "Тип аккаунта"
        self.fields['city'].label = "Город"
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Подтверждение пароля"

        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        self.fields['user_type'].help_text = ''


class CustomAuthenticationForm(AuthenticationForm):
    """Форма входа с русскими подписями."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = "Имя пользователя или @username"
        self.fields['password'].label = "Пароль"


# ========================================
# ✏️ РЕДАКТИРОВАНИЕ ПРОФИЛЯ
# ========================================

BOOTSTRAP_FILE = {'class': 'form-control', 'accept': 'image/*'}
BOOTSTRAP_TEXT = {'class': 'form-control'}
BOOTSTRAP_SELECT = {'class': 'form-select'}
BOOTSTRAP_TEXTAREA = {'class': 'form-control', 'rows': 4}
BOOTSTRAP_CHECKBOX = {'class': 'form-check-input'}
BOOTSTRAP_COLOR = {'class': 'form-control form-control-color', 'type': 'color'}


def normalize_nickname(value):
    """Нормализует @username: убирает @ и пробелы."""
    return (value or '').strip().lstrip('@')


def validate_unique_nickname(nickname, instance_pk=None):
    """Проверяет формат и уникальность публичного @username."""
    if not nickname:
        raise ValidationError('Уникальное имя (@username) обязательно для заполнения.')

    if not NICKNAME_PATTERN.match(nickname):
        raise ValidationError(
            'Имя должно содержать 3–30 символов: латиница, цифры и подчёркивание.'
        )

    qs = CustomUser.objects.filter(nickname__iexact=nickname)
    if instance_pk:
        qs = qs.exclude(pk=instance_pk)
    if qs.exists():
        raise ValidationError('Это @username уже занят. Выберите другое имя.')


def validate_unique_team_username(username, instance_pk=None):
    """Проверяет формат и уникальность @username команды."""
    username = normalize_nickname(username)
    if not username:
        raise ValidationError('Уникальное имя (@username) обязательно для заполнения.')

    if not NICKNAME_PATTERN.match(username):
        raise ValidationError(
            'Имя должно содержать 3–30 символов: латиница, цифры и подчёркивание.'
        )

    qs = Team.objects.filter(username__iexact=username)
    if instance_pk:
        qs = qs.exclude(pk=instance_pk)
    if qs.exists():
        raise ValidationError('Это @username уже занят другой командой.')


def format_phone(value):
    """Форматирует телефон в вид +7 (999) 123-45-67."""
    if not value:
        return ''

    digits = PHONE_DIGITS_PATTERN.sub('', value)
    if digits.startswith('8'):
        digits = '7' + digits[1:]
    if digits.startswith('7'):
        digits = digits[1:]
    digits = digits[:10]

    if len(digits) < 10:
        return value.strip()

    return f'+7 ({digits[0:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:10]}'


def normalize_telegram_link(value):
    """Преобразует @username или ссылку в URL Telegram."""
    value = (value or '').strip()
    if not value:
        return ''
    if value.startswith('http'):
        return value
    username = value.lstrip('@')
    return f'https://t.me/{username}'


class ExtraSocialLinkForm(forms.Form):
    """Дополнительная социальная сеть (название + ссылка)."""

    name = forms.CharField(
        required=False,
        label='Название',
        widget=forms.TextInput(attrs={
            **BOOTSTRAP_TEXT,
            'placeholder': 'Instagram, TikTok...',
        }),
    )
    url = forms.URLField(
        required=False,
        label='Ссылка',
        widget=forms.URLInput(attrs={
            **BOOTSTRAP_TEXT,
            'placeholder': 'https://...',
        }),
        assume_scheme='https',
    )


ExtraSocialLinkFormSet = formset_factory(
    ExtraSocialLinkForm,
    extra=0,
    can_delete=True,
)


class UserProfileForm(forms.ModelForm):
    """Форма редактирования расширенного профиля танцора."""

    social_vk = forms.URLField(
        required=False,
        label='ВКонтакте',
        widget=forms.URLInput(attrs={
            **BOOTSTRAP_TEXT,
            'placeholder': 'https://vk.com/username',
        }),
        assume_scheme='https',
    )
    social_telegram = forms.CharField(
        required=False,
        label='Telegram',
        widget=forms.TextInput(attrs={
            **BOOTSTRAP_TEXT,
            'placeholder': '@username или https://t.me/username',
        }),
    )

    class Meta:
        model = UserProfile
        fields = [
            'photo',
            'cover_gradient_start',
            'cover_gradient_end',
            'bio',
            'dance_level',
            'dance_positions',
            'dance_styles',
            'favorite_groups',
            'experience_start_date',
            'mbti',
            'height',
            'is_available_for_collab',
        ]
        widgets = {
            'photo': forms.FileInput(attrs=BOOTSTRAP_FILE),
            'cover_gradient_start': forms.TextInput(attrs=BOOTSTRAP_COLOR),
            'cover_gradient_end': forms.TextInput(attrs=BOOTSTRAP_COLOR),
            'bio': forms.Textarea(attrs={
                **BOOTSTRAP_TEXTAREA,
                'placeholder': 'Расскажите о себе, своих достижениях и предпочтениях...',
            }),
            'dance_level': forms.Select(attrs=BOOTSTRAP_SELECT),
            'dance_positions': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'Например: центр, бэк-дансер, лидер',
            }),
            'dance_styles': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'Hip-Hop, K-Pop, Jazz Funk (через запятую)',
            }),
            'favorite_groups': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'BTS, BLACKPINK, Stray Kids (через запятую)',
            }),
            'experience_start_date': forms.DateInput(attrs={
                **BOOTSTRAP_TEXT,
                'type': 'date',
            }),
            'mbti': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'Например: ENFP',
                'maxlength': '4',
            }),
            'height': forms.NumberInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': '170',
                'min': '100',
                'max': '250',
            }),
            'is_available_for_collab': forms.CheckboxInput(attrs=BOOTSTRAP_CHECKBOX),
        }
        labels = {
            'photo': 'Фото профиля',
            'cover_gradient_start': 'Цвет градиента (начало)',
            'cover_gradient_end': 'Цвет градиента (конец)',
            'bio': 'О себе',
            'dance_level': 'Уровень подготовки',
            'dance_positions': 'Позиция в танце',
            'dance_styles': 'Стили танцев',
            'favorite_groups': 'Любимые музыкальные группы',
            'experience_start_date': 'Дата начала занятий танцами',
            'mbti': 'Тип MBTI',
            'height': 'Рост (см)',
            'is_available_for_collab': 'Доступен для коллабораций',
        }
        help_texts = {
            'experience_start_date': 'Используется для автоматического расчёта танцевального стажа',
            'mbti': '4 буквы, например ENFP или ISTJ',
            'cover_gradient_start': 'Выберите цвет для градиента обложки профиля',
            'cover_gradient_end': 'Второй цвет градиента обложки',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.social_links:
            links = self.instance.social_links
            self.initial['social_vk'] = links.get('vk', '')
            self.initial['social_telegram'] = links.get('telegram', '')

    def save(self, commit=True):
        instance = super().save(commit=False)
        links = {}

        vk = self.cleaned_data.get('social_vk')
        telegram = self.cleaned_data.get('social_telegram')
        if vk:
            links['vk'] = vk
        if telegram:
            links['telegram'] = normalize_telegram_link(telegram)

        extra_names = self.data.getlist('extra_social_name')
        extra_urls = self.data.getlist('extra_social_url')
        for name, url in zip(extra_names, extra_urls):
            name = (name or '').strip()
            url = (url or '').strip()
            if name and url:
                links[name.lower()] = url

        instance.social_links = links or None
        if commit:
            instance.save()
        return instance


class CustomUserForm(forms.ModelForm):
    """Форма редактирования основных данных пользователя."""

    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'nickname', 'city', 'bio', 'photo',
            'cover_gradient_start', 'cover_gradient_end',
        ]
        widgets = {
            'username': forms.TextInput(attrs=BOOTSTRAP_TEXT),
            'email': forms.EmailInput(attrs=BOOTSTRAP_TEXT),
            'nickname': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'username',
                'data-nickname-field': 'true',
            }),
            'city': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'Москва, Ростов-на-Дону...',
            }),
            'bio': forms.Textarea(attrs={
                **BOOTSTRAP_TEXTAREA,
                'placeholder': 'Кратко о себе...',
            }),
            'photo': forms.FileInput(attrs=BOOTSTRAP_FILE),
            'cover_gradient_start': forms.TextInput(attrs=BOOTSTRAP_COLOR),
            'cover_gradient_end': forms.TextInput(attrs=BOOTSTRAP_COLOR),
        }
        labels = {
            'username': 'Имя пользователя',
            'email': 'Email',
            'nickname': 'Уникальное имя (@username)',
            'city': 'Город',
            'bio': 'О себе (кратко)',
            'photo': 'Фото профиля',
            'cover_gradient_start': 'Цвет градиента (начало)',
            'cover_gradient_end': 'Цвет градиента (конец)',
        }
        help_texts = {
            'nickname': 'Обязательное поле. Одно уникальное имя на весь сайт.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and getattr(self.instance, 'user_type', None) != 'team':
            self.fields['nickname'].required = True

    def clean_nickname(self):
        nickname = normalize_nickname(self.cleaned_data.get('nickname'))
        validate_unique_nickname(nickname, self.instance.pk if self.instance else None)
        return nickname


class SoloProfileEditForm(CustomUserForm):
    """Основные поля сольного танцора без дублирования bio/photo в UserProfile."""

    class Meta(CustomUserForm.Meta):
        fields = ['username', 'email', 'nickname', 'city', 'phone', 'date_of_birth']
        widgets = {
            **CustomUserForm.Meta.widgets,
            'nickname': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'username',
                'data-nickname-field': 'true',
            }),
            'phone': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': '+7 (999) 123-45-67',
                'data-phone-mask': 'true',
                'inputmode': 'tel',
            }),
            'date_of_birth': forms.DateInput(attrs={
                **BOOTSTRAP_TEXT,
                'type': 'date',
            }),
        }
        labels = {
            **CustomUserForm.Meta.labels,
            'nickname': 'Уникальное имя (@username)',
            'phone': 'Телефон',
            'date_of_birth': 'Дата рождения',
        }
        help_texts = {
            'nickname': 'Обязательное поле. Одно уникальное имя на весь сайт — по нему вас находят.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nickname'].required = True

    def clean_phone(self):
        return format_phone(self.cleaned_data.get('phone', ''))


class OrganizerProfileForm(forms.ModelForm):
    """Форма редактирования профиля организатора."""

    class Meta:
        model = OrganizerProfile
        fields = [
            'organization_name',
            'website',
            'social_media',
            'experience_description',
        ]
        widgets = {
            'organization_name': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'Название организации или студии',
            }),
            'website': forms.URLInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'https://example.com',
            }),
            'social_media': forms.Textarea(attrs={
                **BOOTSTRAP_TEXTAREA,
                'rows': 3,
                'placeholder': 'Каждая ссылка с новой строки',
            }),
            'experience_description': forms.Textarea(attrs={
                **BOOTSTRAP_TEXTAREA,
                'placeholder': 'Опыт организации мероприятий, достижения...',
            }),
        }
        labels = {
            'organization_name': 'Название организации',
            'website': 'Сайт',
            'social_media': 'Социальные сети',
            'experience_description': 'Опыт работы',
        }


class SpecialistProfileForm(forms.ModelForm):
    """Форма редактирования профиля специалиста."""

    class Meta:
        model = SpecialistProfile
        fields = [
            'specialization',
            'portfolio_description',
            'price_range',
            'equipment',
            'is_available',
        ]
        widgets = {
            'specialization': forms.Select(attrs=BOOTSTRAP_SELECT),
            'portfolio_description': forms.Textarea(attrs={
                **BOOTSTRAP_TEXTAREA,
                'placeholder': 'Опишите ваше портфолио и опыт...',
            }),
            'price_range': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'Например: от 3000 ₽/час',
            }),
            'equipment': forms.Textarea(attrs={
                **BOOTSTRAP_TEXTAREA,
                'rows': 3,
                'placeholder': 'Камера, объективы, микрофоны...',
            }),
            'is_available': forms.CheckboxInput(attrs=BOOTSTRAP_CHECKBOX),
        }
        labels = {
            'specialization': 'Специализация',
            'portfolio_description': 'Описание портфолио',
            'price_range': 'Ценовой диапазон',
            'equipment': 'Оборудование',
            'is_available': 'Доступен для заказов',
        }


class TeamProfileForm(forms.ModelForm):
    """Форма редактирования профиля танцевальной команды."""

    class Meta:
        model = Team
        fields = [
            'name',
            'username',
            'city',
            'dance_styles',
            'description',
            'logo',
            'cover_gradient_start',
            'cover_gradient_end',
            'founded_year',
            'is_open_recruitment',
            'max_members',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'Название команды',
            }),
            'username': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'username',
                'data-nickname-field': 'true',
            }),
            'city': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'Город',
            }),
            'dance_styles': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'Hip-Hop, K-Pop, Jazz Funk (через запятую)',
            }),
            'description': forms.Textarea(attrs={
                **BOOTSTRAP_TEXTAREA,
                'placeholder': 'Описание команды, история, достижения...',
            }),
            'logo': forms.FileInput(attrs=BOOTSTRAP_FILE),
            'cover_gradient_start': forms.TextInput(attrs=BOOTSTRAP_COLOR),
            'cover_gradient_end': forms.TextInput(attrs=BOOTSTRAP_COLOR),
            'founded_year': forms.NumberInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': '2020',
                'min': '1900',
                'max': '2026',
            }),
            'is_open_recruitment': forms.CheckboxInput(attrs=BOOTSTRAP_CHECKBOX),
            'max_members': forms.NumberInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': '20',
                'min': '2',
                'max': '100',
            }),
        }
        labels = {
            'name': 'Название команды',
            'username': 'Уникальное имя (@username)',
            'city': 'Город',
            'dance_styles': 'Стили танцев',
            'description': 'Описание команды',
            'logo': 'Логотип команды',
            'cover_gradient_start': 'Цвет градиента (начало)',
            'cover_gradient_end': 'Цвет градиента (конец)',
            'founded_year': 'Год основания',
            'is_open_recruitment': 'Открыт набор участников',
            'max_members': 'Максимальное количество участников',
        }
        help_texts = {
            'username': 'Обязательное поле. Одно уникальное имя на весь сайт.',
        }

    def clean_username(self):
        username = normalize_nickname(self.cleaned_data.get('username'))
        validate_unique_team_username(username, self.instance.pk if self.instance else None)
        return username


class TeamMemberAddForm(forms.Form):
    """Добавление участника в команду по @username или логину."""

    user_identifier = forms.CharField(
        label='Пользователь',
        widget=forms.TextInput(attrs={
            **BOOTSTRAP_TEXT,
            'placeholder': '@username или логин',
            'id': 'memberUserInput',
            'autocomplete': 'off',
        }),
    )
    role = forms.ChoiceField(
        choices=TeamMember.ROLE_CHOICES,
        initial='member',
        widget=forms.Select(attrs=BOOTSTRAP_SELECT),
        label='Роль',
    )

    def __init__(self, team, *args, **kwargs):
        self.team = team
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        identifier = normalize_nickname(cleaned.get('user_identifier', ''))
        if not identifier:
            return cleaned

        user = CustomUser.objects.filter(
            Q(nickname__iexact=identifier) | Q(username__iexact=identifier)
        ).first()
        if not user:
            raise ValidationError({'user_identifier': 'Пользователь не найден.'})
        if user.user_type == 'team':
            raise ValidationError({'user_identifier': 'Нельзя добавить аккаунт команды.'})
        if user.pk == self.team.leader_id:
            raise ValidationError({'user_identifier': 'Нельзя добавить профиль команды.'})
        if TeamMember.objects.filter(team=self.team, user=user).exists():
            raise ValidationError({'user_identifier': 'Этот пользователь уже в команде.'})
        if self.team.members_count() >= self.team.max_members:
            raise ValidationError({
                'user_identifier': f'Достигнут лимит участников ({self.team.max_members}).',
            })

        cleaned['user'] = user
        return cleaned

    def save(self):
        return TeamMember.objects.create(
            team=self.team,
            user=self.cleaned_data['user'],
            role=self.cleaned_data['role'],
        )


class TeamApplicationForm(forms.Form):
    """Заявка на вступление в команду."""

    message = forms.CharField(
        required=False,
        label='Сообщение',
        widget=forms.Textarea(attrs={
            **BOOTSTRAP_TEXTAREA,
            'rows': 3,
            'placeholder': 'Расскажите о себе (необязательно)...',
        }),
    )


class PhotoCardForm(forms.ModelForm):
    """Загрузка фотокарточки в профиль."""

    class Meta:
        model = PhotoCard
        fields = [
            'image',
            'caption',
            'album',
            'link_type',
            'link_url',
            'linked_event',
            'linked_cover',
        ]
        widgets = {
            'image': forms.FileInput(attrs=BOOTSTRAP_FILE),
            'caption': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'Подпись к фото...',
            }),
            'album': forms.Select(attrs=BOOTSTRAP_SELECT),
            'link_url': forms.URLInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'https://...',
            }),
            'linked_event': forms.Select(attrs=BOOTSTRAP_SELECT),
            'linked_cover': forms.Select(attrs=BOOTSTRAP_SELECT),
        }
        labels = {
            'image': 'Фото',
            'caption': 'Подпись',
            'album': 'Альбом',
            'link_type': 'Привязка',
            'link_url': 'Ссылка на выступление или страницу',
            'linked_event': 'Мероприятие',
            'linked_cover': 'Кавер',
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['linked_event'].required = False
        self.fields['linked_cover'].required = False
        self.fields['link_url'].required = False
        self.fields['linked_event'].empty_label = '— выберите мероприятие —'
        self.fields['linked_cover'].empty_label = '— выберите кавер —'
        self.fields['album'].required = False
        self.fields['album'].empty_label = '— без альбома —'
        if user:
            self.fields['linked_event'].queryset = Event.objects.all().order_by('-event_date')
            self.fields['linked_cover'].queryset = CoverMedia.objects.filter(
                author=user,
                is_approved=True,
            ).order_by('-created_at')
            self.fields['album'].queryset = PhotoAlbum.objects.filter(user=user).order_by('-created_at')

    def clean(self):
        cleaned = super().clean()
        link_type = cleaned.get('link_type')
        if link_type == 'event' and not cleaned.get('linked_event'):
            raise ValidationError({'linked_event': 'Выберите мероприятие.'})
        if link_type == 'cover' and not cleaned.get('linked_cover'):
            raise ValidationError({'linked_cover': 'Выберите кавер.'})
        if link_type in ('performance', 'url') and not cleaned.get('link_url'):
            raise ValidationError({'link_url': 'Укажите ссылку.'})
        return cleaned


class PhotoAlbumForm(forms.ModelForm):
    """Создание фотоальбома."""

    class Meta:
        model = PhotoAlbum
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                **BOOTSTRAP_TEXT,
                'placeholder': 'Название альбома',
            }),
        }
        labels = {
            'title': 'Название альбома',
        }

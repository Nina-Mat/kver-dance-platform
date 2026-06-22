from django import forms

from django.core.exceptions import ValidationError

from django.forms import formset_factory



from .models import Event

from .utils import validate_audio_file



ALLOWED_LOGO_TYPES = ('image/jpeg', 'image/png', 'image/webp', 'image/gif')

MAX_LOGO_SIZE = 5 * 1024 * 1024



BOOTSTRAP_TEXT = {'class': 'form-control'}

BOOTSTRAP_SELECT = {'class': 'form-select'}

BOOTSTRAP_CHECKBOX = {'class': 'form-check-input'}





class EventForm(forms.ModelForm):

    """Форма создания и редактирования мероприятия организатором."""



    require_audio = forms.BooleanField(

        required=False,

        initial=True,

        label='Требовать аудиотрек в заявке',

        widget=forms.CheckboxInput(attrs=BOOTSTRAP_CHECKBOX),

        help_text='Участник загружает MP3 или WAV (до 50 МБ)',

    )



    class Meta:

        model = Event

        fields = [

            'title',

            'description',

            'event_type',

            'event_date',

            'location',

            'location_lat',

            'location_lng',

            'registration_deadline',

            'logo',

            'is_published',

        ]

        widgets = {

            'title': forms.TextInput(attrs={

                'class': 'form-control',

                'placeholder': 'Название фестиваля, баттла или кастинга',

            }),

            'description': forms.Textarea(attrs={

                'class': 'form-control',

                'rows': 4,

                'placeholder': 'Описание мероприятия, правила участия...',

            }),

            'event_type': forms.RadioSelect(attrs={'class': 'form-check-input'}),

            'event_date': forms.DateTimeInput(attrs={

                'class': 'form-control',

                'type': 'datetime-local',

            }),

            'location': forms.TextInput(attrs={

                'class': 'form-control',

                'placeholder': 'Начните вводить адрес или «онлайн»',

                'id': 'id_location',

                'autocomplete': 'off',

            }),

            'location_lat': forms.HiddenInput(),

            'location_lng': forms.HiddenInput(),

            'registration_deadline': forms.DateTimeInput(attrs={

                'class': 'form-control',

                'type': 'datetime-local',

            }),

            'logo': forms.FileInput(attrs={

                'class': 'form-control',

                'accept': 'image/*',

            }),

            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

        }

        labels = {

            'title': 'Название мероприятия',

            'description': 'Описание',

            'event_type': 'Тип мероприятия',

            'event_date': 'Дата и время проведения',

            'location': 'Место проведения',

            'registration_deadline': 'Дедлайн регистрации',

            'logo': 'Логотип мероприятия',

            'is_published': 'Опубликовать в календаре',

        }

        help_texts = {

            'event_date': 'Эта дата отображается в календаре мероприятий',

            'logo': 'Используется как маркер в календаре (PNG/JPG/WebP, до 5 МБ)',

        }



    def clean_logo(self):

        """Проверяет MIME-тип и размер загружаемого логотипа."""

        logo = self.cleaned_data.get('logo')

        if not logo:

            return logo



        if logo.content_type not in ALLOWED_LOGO_TYPES:

            raise ValidationError('Допустимы только изображения: JPEG, PNG, WebP, GIF.')



        if logo.size > MAX_LOGO_SIZE:

            raise ValidationError('Размер логотипа не должен превышать 5 МБ.')



        return logo



    def clean(self):

        """Проверяет, что дедлайн регистрации раньше даты проведения."""

        cleaned_data = super().clean()

        event_date = cleaned_data.get('event_date')

        registration_deadline = cleaned_data.get('registration_deadline')



        if event_date and registration_deadline and registration_deadline >= event_date:

            raise ValidationError(

                'Дедлайн регистрации должен быть раньше даты проведения мероприятия.'

            )

        location = (cleaned_data.get('location') or '').strip().lower()
        if location in ('онлайн', 'online'):
            cleaned_data['location_lat'] = None
            cleaned_data['location_lng'] = None

        return cleaned_data





class CustomFieldForm(forms.Form):

    """Одно кастомное поле конструктора заявки."""



    FIELD_TYPE_CHOICES = [

        ('text', 'Текст'),

        ('textarea', 'Текст (многострочный)'),

        ('email', 'Email'),

        ('number', 'Число'),

    ]



    label = forms.CharField(

        required=False,

        label='Название поля',

        widget=forms.TextInput(attrs={

            **BOOTSTRAP_TEXT,

            'placeholder': 'Например: Название команды',

        }),

    )

    field_type = forms.ChoiceField(

        choices=FIELD_TYPE_CHOICES,

        label='Тип поля',

        initial='text',

        widget=forms.Select(attrs=BOOTSTRAP_SELECT),

    )

    required = forms.BooleanField(

        required=False,

        label='Обязательное',

        widget=forms.CheckboxInput(attrs=BOOTSTRAP_CHECKBOX),

    )





CustomFieldFormSet = formset_factory(

    CustomFieldForm,

    extra=3,

    max_num=10,

    can_delete=True,

)





class EventApplicationForm(forms.Form):

    """Динамическая форма заявки участника на мероприятие."""



    def __init__(self, event, *args, **kwargs):

        """Создаёт поля формы на основе конфигурации мероприятия.



        Args:

            event: Экземпляр Event с form_fields.

        """

        super().__init__(*args, **kwargs)

        self.event = event



        for field_def in event.get_form_field_defs():

            self.fields[field_def['name']] = self._build_custom_field(field_def)



        if event.requires_audio():

            self.fields['audio_file'] = forms.FileField(

                label='Аудиотрек',

                required=True,

                widget=forms.FileInput(attrs={

                    'class': 'form-control',

                    'accept': 'audio/mpeg,audio/wav,.mp3,.wav',

                }),

                help_text='Формат MP3 или WAV, до 50 МБ',

            )



    def _build_custom_field(self, field_def):

        """Создаёт Django-поле по описанию из JSON-конфига."""

        label = field_def['label']

        required = field_def.get('required', False)

        field_type = field_def.get('type', 'text')



        if field_type == 'textarea':

            return forms.CharField(

                label=label,

                required=required,

                widget=forms.Textarea(attrs={**BOOTSTRAP_TEXT, 'rows': 3}),

            )

        if field_type == 'email':

            return forms.EmailField(

                label=label,

                required=required,

                widget=forms.EmailInput(attrs=BOOTSTRAP_TEXT),

            )

        if field_type == 'number':

            return forms.IntegerField(

                label=label,

                required=required,

                widget=forms.NumberInput(attrs=BOOTSTRAP_TEXT),

            )

        return forms.CharField(

            label=label,

            required=required,

            widget=forms.TextInput(attrs=BOOTSTRAP_TEXT),

        )



    def clean_audio_file(self):

        """Проверяет загруженный аудиотрек."""

        audio = self.cleaned_data.get('audio_file')

        return validate_audio_file(audio)



    def get_form_data(self):

        """Возвращает ответы на кастомные поля (без audio_file)."""

        return {

            key: value

            for key, value in self.cleaned_data.items()

            if key != 'audio_file'

        }


from django.db import models
from django.urls import reverse
from django.utils import timezone

from accounts.models import CustomUser

from .utils import application_audio_upload_to


class Event(models.Model):
    """Мероприятие кавер-дэнс сообщества."""

    EVENT_TYPE_CHOICES = [
        ('battle', 'Баттл'),
        ('casting', 'Кастинг'),
        ('championship', 'Чемпионат'),
        ('festival', 'Фестиваль'),
    ]

    organizer = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='organized_events',
        verbose_name='Организатор',
    )
    title = models.CharField(max_length=200, verbose_name='Название мероприятия')
    description = models.TextField(blank=True, verbose_name='Описание')
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        verbose_name='Тип мероприятия',
    )
    event_date = models.DateTimeField(verbose_name='Дата и время проведения')
    location = models.CharField(
        max_length=200,
        verbose_name='Место проведения',
        help_text='Адрес или «онлайн»',
    )
    location_lat = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Широта',
    )
    location_lng = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Долгота',
    )
    registration_deadline = models.DateTimeField(verbose_name='Дедлайн регистрации')
    form_fields = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Конфигурация полей формы заявки',
    )
    logo = models.ImageField(
        upload_to='events/logos/',
        blank=True,
        null=True,
        verbose_name='Логотип мероприятия',
    )
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Мероприятие'
        verbose_name_plural = 'Мероприятия'
        ordering = ['-event_date']

    def __str__(self):
        return f'{self.title} ({self.event_date.strftime("%d.%m.%Y")})'

    def get_absolute_url(self):
        return reverse('events:detail', kwargs={'pk': self.pk})

    def get_form_field_defs(self):
        """Возвращает список кастомных полей формы заявки."""
        if not self.form_fields:
            return []
        return self.form_fields.get('fields', [])

    def requires_audio(self):
        """True, если для заявки требуется аудиотрек."""
        if not self.form_fields:
            return True
        return self.form_fields.get('require_audio', True)

    @property
    def is_registration_open(self):
        """True, если регистрация на мероприятие ещё открыта."""
        return self.is_published and timezone.now() <= self.registration_deadline


class EventApplication(models.Model):
    """Заявка участника на мероприятие."""

    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('approved', 'Принята'),
        ('rejected', 'Отклонена'),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Мероприятие',
    )
    applicant = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='event_applications',
        verbose_name='Участник',
    )
    form_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Ответы на поля формы',
    )
    audio_file = models.FileField(
        upload_to=application_audio_upload_to,
        blank=True,
        null=True,
        verbose_name='Аудиотрек',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата подачи')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Заявка на мероприятие'
        verbose_name_plural = 'Заявки на мероприятия'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['event', 'applicant'],
                name='unique_event_application_per_user',
            ),
        ]

    def __str__(self):
        return f'{self.applicant.username} → {self.event.title} ({self.get_status_display()})'

    def get_status_badge_class(self):
        """CSS-класс бейджа статуса для шаблонов."""
        return {
            'pending': 'stat-badge',
            'approved': 'stat-badge stat-badge--success',
            'rejected': 'stat-badge stat-badge--danger',
        }.get(self.status, 'stat-badge')

    def get_display_form_data(self):
        """Возвращает ответы формы с человекочитаемыми названиями полей."""
        labels = {
            field['name']: field['label']
            for field in self.event.get_form_field_defs()
        }
        return [
            {
                'label': labels.get(name, name),
                'value': value,
            }
            for name, value in self.form_data.items()
        ]

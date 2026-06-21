# Generated for EventApplication model

import events.utils
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('events', '0002_event_fields_update'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventApplication',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('form_data', models.JSONField(blank=True, default=dict, verbose_name='Ответы на поля формы')),
                ('audio_file', models.FileField(blank=True, null=True, upload_to=events.utils.application_audio_upload_to, verbose_name='Аудиотрек')),
                ('status', models.CharField(choices=[('pending', 'На рассмотрении'), ('approved', 'Принята'), ('rejected', 'Отклонена')], default='pending', max_length=20, verbose_name='Статус')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата подачи')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('applicant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='event_applications', to=settings.AUTH_USER_MODEL, verbose_name='Участник')),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='events.event', verbose_name='Мероприятие')),
            ],
            options={
                'verbose_name': 'Заявка на мероприятие',
                'verbose_name_plural': 'Заявки на мероприятия',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='eventapplication',
            constraint=models.UniqueConstraint(fields=('event', 'applicant'), name='unique_event_application_per_user'),
        ),
    ]

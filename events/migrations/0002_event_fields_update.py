# Generated manually for Event model update

from django.db import migrations, models
from django.utils import timezone


def set_registration_deadline_from_event_date(apps, schema_editor):
    """Устанавливает дедлайн регистрации равным дате проведения для старых записей."""
    Event = apps.get_model('events', 'Event')
    for event in Event.objects.order_by('pk'):
        if event.event_date:
            event.registration_deadline = event.event_date
            event.save(update_fields=['registration_deadline'])


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='event_type',
            field=models.CharField(
                choices=[
                    ('battle', 'Баттл'),
                    ('casting', 'Кастинг'),
                    ('championship', 'Чемпионат'),
                    ('festival', 'Фестиваль'),
                ],
                default='festival',
                max_length=20,
                verbose_name='Тип мероприятия',
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='registration_deadline',
            field=models.DateTimeField(
                default=timezone.now,
                verbose_name='Дедлайн регистрации',
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='form_fields',
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name='Конфигурация полей формы заявки',
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='logo',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='events/logos/',
                verbose_name='Логотип мероприятия',
            ),
        ),
        migrations.AddField(
            model_name='event',
            name='is_published',
            field=models.BooleanField(default=True, verbose_name='Опубликовано'),
        ),
        migrations.RenameField(
            model_name='event',
            old_name='date',
            new_name='event_date',
        ),
        migrations.RunPython(
            set_registration_deadline_from_event_date,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name='event',
            name='status',
        ),
        migrations.AlterField(
            model_name='event',
            name='description',
            field=models.TextField(blank=True, verbose_name='Описание'),
        ),
        migrations.AlterField(
            model_name='event',
            name='title',
            field=models.CharField(max_length=200, verbose_name='Название мероприятия'),
        ),
        migrations.AlterModelOptions(
            name='event',
            options={
                'ordering': ['-event_date'],
                'verbose_name': 'Мероприятие',
                'verbose_name_plural': 'Мероприятия',
            },
        ),
    ]

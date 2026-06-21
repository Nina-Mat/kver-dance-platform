# Generated manually for cover gradients and PhotoCard model

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_eventapplication'),
        ('media_app', '0002_covermedia_mentioned_users'),
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='cover_gradient_end',
            field=models.CharField(default='#8B5CF6', max_length=7, verbose_name='Цвет градиента обложки (конец)'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='cover_gradient_start',
            field=models.CharField(default='#EC4899', max_length=7, verbose_name='Цвет градиента обложки (начало)'),
        ),
        migrations.AddField(
            model_name='team',
            name='cover_gradient_end',
            field=models.CharField(default='#8B5CF6', max_length=7, verbose_name='Цвет градиента обложки (конец)'),
        ),
        migrations.AddField(
            model_name='team',
            name='cover_gradient_start',
            field=models.CharField(default='#EC4899', max_length=7, verbose_name='Цвет градиента обложки (начало)'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='cover_gradient_end',
            field=models.CharField(default='#8B5CF6', max_length=7, verbose_name='Цвет градиента обложки (конец)'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='cover_gradient_start',
            field=models.CharField(default='#EC4899', max_length=7, verbose_name='Цвет градиента обложки (начало)'),
        ),
        migrations.CreateModel(
            name='PhotoCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='photo_cards/', verbose_name='Фото')),
                ('caption', models.CharField(blank=True, max_length=300, verbose_name='Подпись')),
                ('link_type', models.CharField(
                    choices=[
                        ('none', 'Без ссылки'),
                        ('event', 'Мероприятие'),
                        ('cover', 'Кавер'),
                        ('performance', 'Выступление'),
                        ('url', 'Другая ссылка'),
                    ],
                    default='none',
                    max_length=20,
                    verbose_name='Тип ссылки',
                )),
                ('link_url', models.URLField(blank=True, verbose_name='Ссылка')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')),
                ('linked_cover', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='photo_cards',
                    to='media_app.covermedia',
                    verbose_name='Кавер',
                )),
                ('linked_event', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='photo_cards',
                    to='events.event',
                    verbose_name='Мероприятие',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='photo_cards',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Пользователь',
                )),
            ],
            options={
                'verbose_name': 'Фотокарточка',
                'verbose_name_plural': 'Фотокарточки',
                'ordering': ['-created_at'],
            },
        ),
    ]

# Generated manually for photocard engagement

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_notification_event_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='photocard',
            name='likes_kver',
            field=models.PositiveIntegerField(default=0, verbose_name='Лайки на KVER'),
        ),
        migrations.AddField(
            model_name='photocard',
            name='views_kver',
            field=models.PositiveIntegerField(default=0, verbose_name='Просмотры на KVER'),
        ),
        migrations.CreateModel(
            name='PhotoCardComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(verbose_name='Текст комментария')),
                ('is_anonymous', models.BooleanField(default=False, verbose_name='Анонимно')),
                ('is_approved', models.BooleanField(default=False, verbose_name='Прошёл модерацию')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата')),
                ('photo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='accounts.photocard', verbose_name='Фотокарточка')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Автор')),
            ],
            options={
                'verbose_name': 'Комментарий к фото',
                'verbose_name_plural': 'Комментарии к фото',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='PhotoCardCommentLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='accounts.photocardcomment', verbose_name='Комментарий')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photocard_comment_likes', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Лайк комментария к фото',
                'verbose_name_plural': 'Лайки комментариев к фото',
            },
        ),
        migrations.CreateModel(
            name='PhotoCardDailyView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('session_key', models.CharField(blank=True, default='', max_length=40)),
                ('viewer_key', models.CharField(max_length=128, verbose_name='Ключ зрителя')),
                ('view_date', models.DateField(verbose_name='Дата просмотра')),
                ('photo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_views', to='accounts.photocard', verbose_name='Фотокарточка')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='photocard_daily_views', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Дневной просмотр фото',
                'verbose_name_plural': 'Дневные просмотры фото',
            },
        ),
        migrations.CreateModel(
            name='PhotoCardLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('photo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='likes', to='accounts.photocard', verbose_name='Фотокарточка')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='photocard_likes', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Лайк фото',
                'verbose_name_plural': 'Лайки фото',
            },
        ),
        migrations.AddConstraint(
            model_name='photocardcommentlike',
            constraint=models.UniqueConstraint(fields=('user', 'comment'), name='unique_photocard_comment_like'),
        ),
        migrations.AddConstraint(
            model_name='photocarddailyview',
            constraint=models.UniqueConstraint(fields=('photo', 'viewer_key', 'view_date'), name='unique_photocard_daily_view'),
        ),
        migrations.AddConstraint(
            model_name='photocardlike',
            constraint=models.UniqueConstraint(fields=('user', 'photo'), name='unique_photocard_like'),
        ),
    ]

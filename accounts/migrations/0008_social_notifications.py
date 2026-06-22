from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('media_app', '0001_initial'),
        ('accounts', '0007_notification_new_user_registration'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='conversation',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='notifications',
                to='accounts.conversation',
                verbose_name='Диалог',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='cover',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='notifications',
                to='media_app.covermedia',
                verbose_name='Публикация',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='photo',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='notifications',
                to='accounts.photocard',
                verbose_name='Фотокарточка',
            ),
        ),
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                choices=[
                    ('team_application', 'Заявка в команду'),
                    ('team_added', 'Добавлен в команду'),
                    ('event_application', 'Заявка на мероприятие'),
                    ('organizer_verification', 'Подтверждение организатора'),
                    ('organizer_verified', 'Организатор подтверждён'),
                    ('organizer_rejected', 'Организатор отклонён'),
                    ('new_user_registration', 'Новая регистрация'),
                    ('new_subscriber', 'Новый подписчик'),
                    ('photo_like', 'Лайк на фото'),
                    ('photo_comment', 'Комментарий к фото'),
                    ('cover_like', 'Лайк на публикацию'),
                    ('cover_comment', 'Комментарий к публикации'),
                    ('new_message', 'Новое сообщение'),
                ],
                max_length=30,
                verbose_name='Тип',
            ),
        ),
    ]

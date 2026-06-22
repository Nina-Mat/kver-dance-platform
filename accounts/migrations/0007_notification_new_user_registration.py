# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_photocard_engagement'),
    ]

    operations = [
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
                ],
                max_length=30,
                verbose_name='Тип',
            ),
        ),
    ]

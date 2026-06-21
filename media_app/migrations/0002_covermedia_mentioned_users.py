# Generated for mentioned_users M2M on CoverMedia

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('media_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='covermedia',
            name='mentioned_users',
            field=models.ManyToManyField(
                blank=True,
                related_name='mentioned_in_covers',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Упомянутые пользователи',
            ),
        ),
    ]

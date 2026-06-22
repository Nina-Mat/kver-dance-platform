# Generated manually for reliable daily view tracking

from django.db import migrations, models


def backfill_viewer_keys(apps, schema_editor):
    CoverMediaDailyView = apps.get_model('media_app', 'CoverMediaDailyView')
    for row in CoverMediaDailyView.objects.all():
        if row.user_id:
            viewer_key = f'user:{row.user_id}'
        else:
            viewer_key = f'session:{row.session_key or "anon"}'
        CoverMediaDailyView.objects.filter(pk=row.pk).update(viewer_key=viewer_key)


class Migration(migrations.Migration):

    dependencies = [
        ('media_app', '0005_cover_media_daily_view'),
    ]

    operations = [
        migrations.AddField(
            model_name='covermediadailyview',
            name='viewer_key',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.RunPython(backfill_viewer_keys, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='covermediadailyview',
            name='viewer_key',
            field=models.CharField(max_length=128, verbose_name='Ключ зрителя'),
        ),
        migrations.RemoveConstraint(
            model_name='covermediadailyview',
            name='unique_cover_daily_view_user',
        ),
        migrations.RemoveConstraint(
            model_name='covermediadailyview',
            name='unique_cover_daily_view_session',
        ),
        migrations.AddConstraint(
            model_name='covermediadailyview',
            constraint=models.UniqueConstraint(
                fields=('media', 'viewer_key', 'view_date'),
                name='unique_cover_daily_view',
            ),
        ),
    ]

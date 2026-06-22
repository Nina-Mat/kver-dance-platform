# Generated manually

from django.db import migrations, models


def backfill_cover_comment_authors(apps, schema_editor):
    User = apps.get_model('accounts', 'CustomUser')
    Team = apps.get_model('accounts', 'Team')
    Comment = apps.get_model('media_app', 'Comment')

    team_usernames = {
        row['leader_id']: row['username']
        for row in Team.objects.values('leader_id', 'username')
        if row['username']
    }

    for comment in Comment.objects.filter(
        user_id__isnull=False,
        is_anonymous=False,
        author_display_name='',
    ).iterator():
        user = User.objects.filter(pk=comment.user_id).first()
        if not user:
            continue
        if user.user_type == 'team':
            display = team_usernames.get(user.pk) or user.username
        else:
            display = user.username
        Comment.objects.filter(pk=comment.pk).update(author_display_name=display)


class Migration(migrations.Migration):

    dependencies = [
        ('media_app', '0006_covermediadailyview_viewer_key'),
        ('accounts', '0009_unify_usernames'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='author_display_name',
            field=models.CharField(
                blank=True,
                help_text='Сохраняется при удалении аккаунта автора.',
                max_length=150,
                verbose_name='Имя автора (снимок)',
            ),
        ),
        migrations.RunPython(backfill_cover_comment_authors, migrations.RunPython.noop),
    ]

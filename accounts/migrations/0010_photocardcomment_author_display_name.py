# Generated manually

from django.db import migrations, models


def backfill_photocard_comment_authors(apps, schema_editor):
    User = apps.get_model('accounts', 'CustomUser')
    Team = apps.get_model('accounts', 'Team')
    PhotoCardComment = apps.get_model('accounts', 'PhotoCardComment')

    team_usernames = {
        row['leader_id']: row['username']
        for row in Team.objects.values('leader_id', 'username')
        if row['username']
    }

    for comment in PhotoCardComment.objects.filter(
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
        PhotoCardComment.objects.filter(pk=comment.pk).update(author_display_name=display)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_unify_usernames'),
    ]

    operations = [
        migrations.AddField(
            model_name='photocardcomment',
            name='author_display_name',
            field=models.CharField(
                blank=True,
                help_text='Сохраняется при удалении аккаунта автора.',
                max_length=150,
                verbose_name='Имя автора (снимок)',
            ),
        ),
        migrations.RunPython(backfill_photocard_comment_authors, migrations.RunPython.noop),
    ]

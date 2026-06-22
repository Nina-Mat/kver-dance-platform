"""Приводит существующие аккаунты к единому username (логин = @username)."""

from django.db import migrations


def unify_usernames(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')
    Team = apps.get_model('accounts', 'Team')

    for team in Team.objects.select_related('leader').iterator():
        leader = team.leader
        if team.username and leader.username != team.username:
            conflict = CustomUser.objects.filter(
                username__iexact=team.username,
            ).exclude(pk=leader.pk).exists()
            if not conflict:
                leader.username = team.username
                leader.save(update_fields=['username'])
        leader.nickname = None
        leader.first_name = ''
        leader.last_name = ''
        leader.save(update_fields=['nickname', 'first_name', 'last_name'])

    for user in CustomUser.objects.exclude(user_type='team').iterator():
        preferred = user.nickname or user.username
        if preferred and user.username != preferred:
            user_conflict = CustomUser.objects.filter(
                username__iexact=preferred,
            ).exclude(pk=user.pk).exists()
            team_conflict = Team.objects.filter(username__iexact=preferred).exists()
            if not user_conflict and not team_conflict:
                user.username = preferred
        user.nickname = None
        user.first_name = ''
        user.last_name = ''
        user.save(update_fields=['username', 'nickname', 'first_name', 'last_name'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_social_notifications'),
    ]

    operations = [
        migrations.RunPython(unify_usernames, migrations.RunPython.noop),
    ]

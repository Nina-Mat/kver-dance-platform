from django import template
from django.db.models import Q
from django.urls import reverse
from django.utils.safestring import mark_safe

from accounts.models import CustomUser
from media_app.utils import MENTION_PATTERN

register = template.Library()


@register.filter
def linkify_mentions(text):
    """Преобразует @username в ссылки на профили."""
    if not text:
        return ''

    usernames = MENTION_PATTERN.findall(text)
    user_map = {}
    if usernames:
        query = Q()
        for name in usernames:
            query |= Q(username__iexact=name) | Q(nickname__iexact=name)
        for user in CustomUser.objects.filter(query):
            user_map[user.username.lower()] = user
            if user.nickname:
                user_map[user.nickname.lower()] = user

    def replace(match):
        name = match.group(1)
        user = user_map.get(name.lower())
        if user:
            url = reverse('accounts:profile', kwargs={'pk': user.pk})
            return f'<a href="{url}" class="mention-link">@{name}</a>'
        return f'@{name}'

    return mark_safe(MENTION_PATTERN.sub(replace, text))

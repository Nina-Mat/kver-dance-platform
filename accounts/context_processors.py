"""Контекст для шаблонов — счётчики и глобальные данные."""

from django.db.models import Q


def messenger_unread(request):
    """Количество непрочитанных сообщений для бокового меню."""
    if not request.user.is_authenticated:
        return {'unread_messages_count': 0}

    from .models import Message

    count = Message.objects.filter(
        is_read=False,
    ).exclude(
        sender=request.user,
    ).filter(
        Q(conversation__participant1=request.user)
        | Q(conversation__participant2=request.user),
    ).count()

    return {'unread_messages_count': count}


def linked_accounts(request):
    """Аккаунты, между которыми можно переключаться."""
    if not request.user.is_authenticated:
        return {'linked_accounts': []}

    from .multi_account import get_linked_accounts
    return {'linked_accounts': get_linked_accounts(request)}


def notifications_context(request):
    """Непрочитанные уведомления и последние для колокольчика."""
    if not request.user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'recent_notifications': [],
        }

    from .models import Notification

    qs = Notification.objects.filter(
        recipient=request.user,
    ).select_related('team', 'actor', 'application')

    return {
        'unread_notifications_count': qs.filter(is_read=False).count(),
        'recent_notifications': qs[:10],
    }

"""Проверка и уведомления для организаторов мероприятий."""

from core.utils import get_kver_admin_users

from .notifications import create_notification


def organizer_is_verified(user):
    """True, если организатор подтверждён администрацией."""
    if not user.is_authenticated or user.user_type != 'organizer':
        return False
    profile = getattr(user, 'organizer_profile', None)
    if profile is None:
        return False
    return profile.is_verified


def organizer_can_create_events(user):
    return organizer_is_verified(user)


def notify_admin_new_organizer(organizer):
    """Отправляет администрации запрос на подтверждение организатора."""
    display_name = organizer.public_username
    for admin in get_kver_admin_users():
        if admin.pk == organizer.pk:
            continue
        create_notification(
            recipient=admin,
            notification_type='organizer_verification',
            title='Новый организатор',
            message=(
                f'@{display_name} зарегистрировался как организатор мероприятий '
                f'и ожидает подтверждения аккаунта.'
            ),
            actor=organizer,
        )

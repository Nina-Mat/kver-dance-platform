"""Уведомления администрации KVER о событиях на платформе."""

from core.utils import get_kver_admin_user

from .models import CustomUser
from .notifications import create_notification

USER_TYPE_LABELS = dict(CustomUser.USER_TYPE_CHOICES)


def _get_registration_display_name(user):
    if user.user_type == 'team':
        team = getattr(user, 'team_profile', None)
        if team:
            return team.username or team.name
    return user.nickname or user.username


def notify_admin_new_user(user):
    """Сообщает администрации о регистрации нового пользователя."""
    admin = get_kver_admin_user()
    if not admin or admin.pk == user.pk:
        return

    # Организаторы получают отдельное уведомление с кнопками подтверждения.
    if user.user_type == 'organizer':
        return

    display_name = _get_registration_display_name(user)
    type_label = USER_TYPE_LABELS.get(user.user_type, user.user_type)

    create_notification(
        recipient=admin,
        notification_type='new_user_registration',
        title='Новая регистрация',
        message=f'@{display_name} зарегистрировался на KVER ({type_label}).',
        actor=user,
    )

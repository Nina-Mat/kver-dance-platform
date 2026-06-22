"""Создание in-app уведомлений."""

from .models import Notification


def create_notification(
    *,
    recipient,
    notification_type,
    title,
    message,
    team=None,
    application=None,
    event=None,
    actor=None,
    photo=None,
    cover=None,
    conversation=None,
):
    return Notification.objects.create(
        recipient=recipient,
        notification_type=notification_type,
        title=title,
        message=message,
        team=team,
        application=application,
        event=event,
        actor=actor,
        photo=photo,
        cover=cover,
        conversation=conversation,
    )

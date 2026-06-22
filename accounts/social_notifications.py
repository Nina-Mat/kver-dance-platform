"""Уведомления о подписках, лайках, комментариях и сообщениях."""

from .notifications import create_notification


def _actor_name(user):
    return user.public_username


def notify_new_subscriber(target, subscriber):
    if target.pk == subscriber.pk:
        return
    create_notification(
        recipient=target,
        notification_type='new_subscriber',
        title='Новый подписчик',
        message=f'@{_actor_name(subscriber)} подписался на вас.',
        actor=subscriber,
    )


def notify_photo_like(photo, actor):
    if not photo.user_id or photo.user_id == actor.pk:
        return
    create_notification(
        recipient=photo.user,
        notification_type='photo_like',
        title='Новый лайк',
        message=f'@{_actor_name(actor)} поставил(а) лайк вашему фото.',
        actor=actor,
        photo=photo,
    )


def notify_photo_comment(photo, actor):
    if not photo.user_id or photo.user_id == actor.pk:
        return
    create_notification(
        recipient=photo.user,
        notification_type='photo_comment',
        title='Новый комментарий',
        message=f'@{_actor_name(actor)} прокомментировал(а) ваше фото.',
        actor=actor,
        photo=photo,
    )


def notify_cover_like(cover, actor):
    if not cover.author_id or cover.author_id == actor.pk:
        return
    create_notification(
        recipient=cover.author,
        notification_type='cover_like',
        title='Новый лайк',
        message=f'@{_actor_name(actor)} поставил(а) лайк вашей публикации.',
        actor=actor,
        cover=cover,
    )


def notify_cover_comment(cover, actor):
    if not cover.author_id or cover.author_id == actor.pk:
        return
    create_notification(
        recipient=cover.author,
        notification_type='cover_comment',
        title='Новый комментарий',
        message=f'@{_actor_name(actor)} прокомментировал(а) вашу публикацию.',
        actor=actor,
        cover=cover,
    )


def notify_new_message(conversation, sender, text):
    recipient = conversation.other_participant(sender)
    if recipient.pk == sender.pk:
        return
    preview = text if len(text) <= 120 else f'{text[:117]}...'
    create_notification(
        recipient=recipient,
        notification_type='new_message',
        title='Новое сообщение',
        message=f'@{_actor_name(sender)}: {preview}',
        actor=sender,
        conversation=conversation,
    )

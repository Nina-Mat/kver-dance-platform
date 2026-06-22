from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import CustomUser, PhotoCardComment


@receiver(pre_delete, sender=CustomUser)
def snapshot_comment_authors_on_user_delete(sender, instance, **kwargs):
    """Сохраняет @username автора в комментариях перед удалением аккаунта."""
    display = instance.public_username
    PhotoCardComment.objects.filter(
        user=instance,
        is_anonymous=False,
    ).exclude(author_display_name=display).update(author_display_name=display)

    from media_app.models import Comment

    Comment.objects.filter(
        user=instance,
        is_anonymous=False,
    ).exclude(author_display_name=display).update(author_display_name=display)

"""Контекст для media_app в шаблонах."""

from media_app.moderation import MODERATION_POLICY_MESSAGE, get_stop_words_json


def moderation_context(request):
    return {
        'moderation_stop_words_json': get_stop_words_json(),
        'moderation_policy_message': MODERATION_POLICY_MESSAGE,
    }


def liked_covers_context(request):
    if not request.user.is_authenticated:
        return {'user_liked_cover_ids': frozenset()}

    from media_app.models import CoverLike

    return {
        'user_liked_cover_ids': frozenset(
            CoverLike.objects.filter(user=request.user).values_list('media_id', flat=True)
        ),
    }

"""Учёт просмотров фотокарточек."""

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils import timezone

from media_app.utils import get_viewer_key

from .models import PhotoCard, PhotoCardDailyView


def record_photo_card_view(request, photo):
    """Увеличивает счётчик просмотров, если зритель ещё не смотрел фото сегодня."""
    today = timezone.localdate()
    viewer_key = get_viewer_key(request)

    if PhotoCardDailyView.objects.filter(
        photo_id=photo.pk,
        viewer_key=viewer_key,
        view_date=today,
    ).exists():
        return

    try:
        with transaction.atomic():
            PhotoCardDailyView.objects.create(
                photo=photo,
                viewer_key=viewer_key,
                view_date=today,
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key or '',
            )
            PhotoCard.objects.filter(pk=photo.pk).update(views_kver=F('views_kver') + 1)
    except IntegrityError:
        return

    photo.refresh_from_db(fields=['views_kver'])

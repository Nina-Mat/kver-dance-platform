"""Сборка гибридной ленты рекомендаций."""

from dataclasses import dataclass
from datetime import datetime

from django.db.models import Count, Q

from accounts.models import PhotoCard, Subscription
from media_app.models import CoverMedia


@dataclass
class FeedItem:
    """Элемент ленты: фотокарточка, кавер или выступление."""

    item_type: str
    obj: object
    created_at: datetime
    author_id: int
    boosted: bool


def get_subscribed_author_ids(user):
    """ID авторов, на которых подписан пользователь."""
    if not user.is_authenticated:
        return set()
    return set(
        Subscription.objects.filter(subscriber=user).values_list('target_id', flat=True)
    )


def build_feed_items(user, limit=50):
    """
    Смешивает фотокарточки, каверы (YouTube) и выступления (загрузки).
    Сортировка: от новых к старым.
    """
    subscribed = get_subscribed_author_ids(user)
    items = []

    photo_cards = PhotoCard.objects.select_related('user').annotate(
        comments_count=Count('comments', filter=Q(comments__is_approved=True)),
    ).order_by('-created_at')[:100]
    for card in photo_cards:
        items.append(FeedItem(
            'photocard', card, card.created_at, card.user_id,
            card.user_id in subscribed,
        ))

    covers = CoverMedia.objects.filter(
        is_approved=True,
        source_type='youtube',
    ).select_related('author').prefetch_related('mentioned_users').order_by('-created_at')[:100]
    for cover in covers:
        items.append(FeedItem(
            'cover', cover, cover.created_at, cover.author_id,
            cover.author_id in subscribed,
        ))

    performances = CoverMedia.objects.filter(
        is_approved=True,
        source_type='upload',
        feed_type='performance',
    ).select_related('author').prefetch_related('mentioned_users').order_by('-created_at')[:100]
    for perf in performances:
        items.append(FeedItem(
            'performance', perf, perf.created_at, perf.author_id,
            perf.author_id in subscribed,
        ))

    uploads_as_covers = CoverMedia.objects.filter(
        is_approved=True,
        source_type='upload',
        feed_type='cover',
    ).select_related('author').prefetch_related('mentioned_users').order_by('-created_at')[:100]
    for cover in uploads_as_covers:
        items.append(FeedItem(
            'cover', cover, cover.created_at, cover.author_id,
            cover.author_id in subscribed,
        ))

    items.sort(key=lambda item: item.created_at, reverse=True)
    return items[:limit]


def build_covers_feed(limit=30):
    """Рекомендации каверов (YouTube-ссылки)."""
    return CoverMedia.objects.filter(
        is_approved=True,
        source_type='youtube',
    ).select_related('author').prefetch_related(
        'mentioned_users',
    ).order_by('?')[:limit]


def build_performances_feed(limit=30):
    """Рекомендации выступлений (загруженные видео)."""
    return CoverMedia.objects.filter(
        is_approved=True,
        source_type='upload',
        feed_type='performance',
    ).select_related('author').prefetch_related(
        'mentioned_users',
    ).order_by('?')[:limit]

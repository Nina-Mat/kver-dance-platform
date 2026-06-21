"""Сборка гибридной ленты рекомендаций."""

import random
from dataclasses import dataclass
from datetime import datetime

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


def _score_item(item):
    """Чем выше score, тем выше в ленте. Подписки получают буст."""
    base = item.created_at.timestamp()
    if item.boosted:
        base += 86400 * 14
    base += random.uniform(0, 7200)
    return base


def build_feed_items(user, limit=50):
    """
    Смешивает фотокарточки, каверы (YouTube) и выступления (загрузки).
    Контент подписок всплывает чаще — как в Instagram/TikTok.
    """
    subscribed = get_subscribed_author_ids(user)
    items = []

    photo_cards = PhotoCard.objects.select_related('user').order_by('-created_at')[:100]
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
    ).select_related('author').prefetch_related('mentioned_users').order_by('-created_at')[:100]
    for perf in performances:
        items.append(FeedItem(
            'performance', perf, perf.created_at, perf.author_id,
            perf.author_id in subscribed,
        ))

    items.sort(key=_score_item, reverse=True)
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
    ).select_related('author').prefetch_related(
        'mentioned_users',
    ).order_by('?')[:limit]

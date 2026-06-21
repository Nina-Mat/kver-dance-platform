"""Глобальный поиск по платформе (как во ВКонтакте)."""

from dataclasses import dataclass

from django.db.models import Q
from django.urls import reverse

from accounts.models import CustomUser, Team, PhotoCard, UserProfile
from events.models import Event
from media_app.models import CoverMedia


@dataclass
class SearchResult:
    """Один результат поиска."""

    category: str
    category_label: str
    title: str
    subtitle: str
    url: str
    image_url: str = ''


CATEGORY_LABELS = {
    'users': 'Люди',
    'teams': 'Команды',
    'covers': 'Каверы',
    'performances': 'Выступления',
    'photos': 'Фотокарточки',
    'events': 'Мероприятия',
}


def _user_label(user):
    nickname = user.nickname or user.username
    name = user.get_full_name().strip()
    if name and name != user.username:
        return f'@{nickname} · {name}'
    return f'@{nickname}'


def _user_subtitle(user):
    return user.get_user_type_display()


def search_users(query, limit=5):
    q = query.strip()
    if len(q) < 2:
        return []

    filters = (
        Q(username__icontains=q)
        | Q(nickname__icontains=q)
        | Q(first_name__icontains=q)
        | Q(last_name__icontains=q)
        | Q(city__icontains=q)
    )
    if q.startswith('@'):
        filters |= Q(nickname__icontains=q[1:])

    users = CustomUser.objects.filter(filters).exclude(
        user_type='team',
    ).distinct().order_by('username')[:limit]

    results = []
    for user in users:
        photo = ''
        if user.user_type == 'solo':
            try:
                profile = user.profile
                if profile.photo:
                    photo = profile.photo.url
            except UserProfile.DoesNotExist:
                pass
        if not photo and user.photo:
            photo = user.photo.url

        results.append(SearchResult(
            category='users',
            category_label=CATEGORY_LABELS['users'],
            title=_user_label(user),
            subtitle=_user_subtitle(user),
            url=reverse('accounts:profile', kwargs={'pk': user.pk}),
            image_url=photo,
        ))
    return results


def search_teams(query, limit=5):
    q = query.strip()
    if len(q) < 2:
        return []

    teams = Team.objects.filter(
        Q(name__icontains=q) | Q(username__icontains=q) | Q(city__icontains=q),
    ).order_by('name')[:limit]

    return [
        SearchResult(
            category='teams',
            category_label=CATEGORY_LABELS['teams'],
            title=team.name,
            subtitle=f'@{team.username}' + (f' · {team.city}' if team.city else ''),
            url=reverse('accounts:team_profile', kwargs={'pk': team.pk}),
            image_url=team.logo.url if team.logo else '',
        )
        for team in teams
    ]


def search_covers(query, limit=5):
    q = query.strip()
    if len(q) < 2:
        return []

    media = CoverMedia.objects.filter(
        is_approved=True,
        source_type='youtube',
    ).filter(
        Q(title__icontains=q)
        | Q(description__icontains=q)
        | Q(tags__icontains=q)
        | Q(author__username__icontains=q)
        | Q(author__nickname__icontains=q),
    ).select_related('author').order_by('-created_at')[:limit]

    return [
        SearchResult(
            category='covers',
            category_label=CATEGORY_LABELS['covers'],
            title=cover.title,
            subtitle=f'@{cover.author.nickname or cover.author.username}',
            url=reverse('media_app:detail', kwargs={'pk': cover.pk}),
            image_url=cover.thumbnail_url or '',
        )
        for cover in media
    ]


def search_performances(query, limit=5):
    q = query.strip()
    if len(q) < 2:
        return []

    media = CoverMedia.objects.filter(
        is_approved=True,
        source_type='upload',
    ).filter(
        Q(title__icontains=q)
        | Q(description__icontains=q)
        | Q(tags__icontains=q)
        | Q(author__username__icontains=q)
        | Q(author__nickname__icontains=q),
    ).select_related('author').order_by('-created_at')[:limit]

    results = []
    for cover in media:
        image = cover.thumbnail_url or ''
        if cover.cover_image:
            image = cover.cover_image.url
        results.append(SearchResult(
            category='performances',
            category_label=CATEGORY_LABELS['performances'],
            title=cover.title,
            subtitle=f'@{cover.author.nickname or cover.author.username}',
            url=reverse('media_app:detail', kwargs={'pk': cover.pk}),
            image_url=image,
        ))
    return results


def search_photos(query, limit=5):
    q = query.strip()
    if len(q) < 2:
        return []

    photos = PhotoCard.objects.filter(
        Q(caption__icontains=q)
        | Q(user__username__icontains=q)
        | Q(user__nickname__icontains=q),
    ).select_related('user').order_by('-created_at')[:limit]

    return [
        SearchResult(
            category='photos',
            category_label=CATEGORY_LABELS['photos'],
            title=photo.caption or 'Фотокарточка',
            subtitle=f'@{photo.user.nickname or photo.user.username}',
            url=f"{reverse('accounts:profile', kwargs={'pk': photo.user.pk})}#photocards",
            image_url=photo.image.url,
        )
        for photo in photos
    ]


def search_events(query, limit=5):
    q = query.strip()
    if len(q) < 2:
        return []

    events = Event.objects.filter(
        Q(title__icontains=q)
        | Q(location__icontains=q)
        | Q(description__icontains=q),
    ).order_by('-event_date')[:limit]

    return [
        SearchResult(
            category='events',
            category_label=CATEGORY_LABELS['events'],
            title=event.title,
            subtitle=event.location or 'Мероприятие',
            url=event.get_absolute_url(),
            image_url=event.logo.url if getattr(event, 'logo', None) and event.logo else '',
        )
        for event in events
    ]


def global_search(query, limits=None):
    """
    Поиск по всем категориям.
    limits — dict с лимитами на категорию (для подсказок меньше, для страницы больше).
    """
    if limits is None:
        limits = {
            'users': 8,
            'teams': 5,
            'covers': 8,
            'performances': 8,
            'photos': 8,
            'events': 5,
        }

    if not query or len(query.strip()) < 2:
        return {}

    grouped = {
        'users': search_users(query, limits.get('users', 5)),
        'teams': search_teams(query, limits.get('teams', 5)),
        'covers': search_covers(query, limits.get('covers', 5)),
        'performances': search_performances(query, limits.get('performances', 5)),
        'photos': search_photos(query, limits.get('photos', 5)),
        'events': search_events(query, limits.get('events', 5)),
    }
    return {key: val for key, val in grouped.items() if val}


def flatten_results(grouped):
    """Плоский список результатов для подсказок."""
    flat = []
    for items in grouped.values():
        flat.extend(items)
    return flat


def results_to_json(grouped):
    """Сериализация для AJAX-подсказок."""
    data = []
    for category, items in grouped.items():
        for item in items:
            data.append({
                'category': item.category,
                'category_label': item.category_label,
                'title': item.title,
                'subtitle': item.subtitle,
                'url': item.url,
                'image_url': item.image_url,
            })
    return data

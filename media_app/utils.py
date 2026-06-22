"""Утилиты media_app: YouTube API, упоминания @username."""

import logging
import re

from django.conf import settings
from django.db.models import Q

logger = logging.getLogger(__name__)

MENTION_PATTERN = re.compile(r'@([\w.-]+)')

ALLOWED_VIDEO_TYPES = (
    'video/mp4',
    'video/webm',
    'video/quicktime',
    'video/x-msvideo',
)
ALLOWED_VIDEO_EXTENSIONS = ('.mp4', '.webm', '.mov', '.avi')
MAX_VIDEO_SIZE = 200 * 1024 * 1024


def parse_youtube_url(url):
    """Извлекает video_id из YouTube URL."""
    if not url:
        return None
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def format_youtube_duration(iso_duration):
    """Преобразует ISO 8601 длительность YouTube в читаемый формат."""
    if not iso_duration:
        return ''

    match = re.match(
        r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?',
        iso_duration,
    )
    if not match:
        return iso_duration

    hours, minutes, seconds = (int(part or 0) for part in match.groups())
    if hours:
        return f'{hours}:{minutes:02d}:{seconds:02d}'
    return f'{minutes}:{seconds:02d}'


def get_youtube_fallback_thumbnail(video_id):
    """Возвращает стандартное превью YouTube без API."""
    return f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg'


def fetch_youtube_metadata(video_id):
    """Получает метаданные видео через YouTube Data API v3."""
    api_key = getattr(settings, 'YOUTUBE_API_KEY', '')
    if not api_key or 'ТВОЙ_КЛЮЧ' in api_key:
        return {
            'title': '',
            'description': '',
            'thumbnail_url': get_youtube_fallback_thumbnail(video_id),
            'duration': '',
            'youtube_views': 0,
            'youtube_likes': 0,
        }

    try:
        from googleapiclient.discovery import build

        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.videos().list(
            part='snippet,contentDetails,statistics',
            id=video_id,
        )
        response = request.execute()

        if response.get('items'):
            item = response['items'][0]
            return {
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'thumbnail_url': item['snippet']['thumbnails']['high']['url'],
                'duration': format_youtube_duration(item['contentDetails']['duration']),
                'youtube_views': int(item['statistics'].get('viewCount', 0)),
                'youtube_likes': int(item['statistics'].get('likeCount', 0)),
            }
    except Exception as exc:
        logger.warning('YouTube API error for %s: %s', video_id, exc)

    return {
        'title': '',
        'description': '',
        'thumbnail_url': get_youtube_fallback_thumbnail(video_id),
        'duration': '',
        'youtube_views': 0,
        'youtube_likes': 0,
    }


def extract_mention_usernames(*texts):
    """Извлекает уникальные @username из переданных текстов."""
    usernames = []
    for text in texts:
        if text:
            usernames.extend(MENTION_PATTERN.findall(text))
    return list(dict.fromkeys(usernames))


def resolve_mentioned_users(*texts):
    """Находит пользователей по @username или @nickname."""
    from accounts.models import CustomUser

    usernames = extract_mention_usernames(*texts)
    if not usernames:
        return CustomUser.objects.none()

    query = Q()
    for name in usernames:
        query |= Q(username__iexact=name) | Q(nickname__iexact=name)
    return CustomUser.objects.filter(query).distinct()


def validate_video_file(video_file):
    """Проверяет MIME-тип, расширение и размер видеофайла."""
    from django.core.exceptions import ValidationError
    from pathlib import Path

    if not video_file:
        return video_file

    ext = Path(video_file.name).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValidationError('Допустимы видеофайлы: MP4, WebM, MOV, AVI.')

    content_type = getattr(video_file, 'content_type', '')
    if content_type and content_type not in ALLOWED_VIDEO_TYPES:
        raise ValidationError('Недопустимый формат видеофайла.')

    if video_file.size > MAX_VIDEO_SIZE:
        raise ValidationError('Размер видеофайла не должен превышать 200 МБ.')

    return video_file


def get_viewer_key(request):
    """Стабильный идентификатор зрителя для учёта просмотров."""
    if request.user.is_authenticated:
        return f'user:{request.user.pk}'
    if not request.session.session_key:
        request.session.save()
    return f'session:{request.session.session_key}'


def record_cover_view(request, cover):
    """Увеличивает счётчик просмотров, если пользователь ещё не смотрел пост сегодня."""
    from django.db import IntegrityError, transaction
    from django.db.models import F
    from django.utils import timezone

    from .models import CoverMedia, CoverMediaDailyView

    today = timezone.localdate()
    viewer_key = get_viewer_key(request)

    if CoverMediaDailyView.objects.filter(
        media_id=cover.pk,
        viewer_key=viewer_key,
        view_date=today,
    ).exists():
        return

    try:
        with transaction.atomic():
            CoverMediaDailyView.objects.create(
                media=cover,
                viewer_key=viewer_key,
                view_date=today,
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key or '',
            )
            CoverMedia.objects.filter(pk=cover.pk).update(views_kver=F('views_kver') + 1)
    except IntegrityError:
        return

    cover.refresh_from_db(fields=['views_kver'])

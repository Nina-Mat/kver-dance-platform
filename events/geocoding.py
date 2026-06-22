"""Геокодирование адресов через OpenStreetMap Nominatim."""

import requests

NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
USER_AGENT = 'KVER/1.0 (cover-dance community platform)'


def search_locations(query, limit=5):
    """Возвращает подсказки адресов для поля места проведения."""
    query = (query or '').strip()
    if len(query) < 3:
        return []
    if query.lower() in ('онлайн', 'online'):
        return []

    response = requests.get(
        NOMINATIM_URL,
        params={
            'q': query,
            'format': 'json',
            'limit': limit,
            'accept-language': 'ru',
        },
        headers={'User-Agent': USER_AGENT},
        timeout=8,
    )
    response.raise_for_status()

    results = []
    for item in response.json():
        results.append({
            'label': item.get('display_name', ''),
            'lat': float(item['lat']),
            'lng': float(item['lon']),
        })
    return results

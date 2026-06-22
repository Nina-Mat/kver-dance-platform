"""Контекст для шаблонов core."""

from core.utils import get_kver_admin_user


def kver_admin_context(request):
    return {'kver_admin_user': get_kver_admin_user()}

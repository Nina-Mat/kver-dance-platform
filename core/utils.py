"""Утилиты приложения core."""


def get_kver_admin_user():
    """Возвращает аккаунт администрации KVER (суперпользователь)."""
    from django.conf import settings

    from accounts.models import CustomUser

    admin_id = getattr(settings, 'KVER_ADMIN_USER_ID', None)
    if admin_id:
        user = CustomUser.objects.filter(pk=admin_id, is_superuser=True, is_active=True).first()
        if user:
            return user

    return CustomUser.objects.filter(is_superuser=True, is_active=True).order_by('pk').first()


def is_kver_admin(user):
    """True, если пользователь — официальный аккаунт администрации."""
    if not user or not user.is_authenticated or not user.is_superuser:
        return False
    admin = get_kver_admin_user()
    return admin is not None and admin.pk == user.pk

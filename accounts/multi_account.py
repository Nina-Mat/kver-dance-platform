"""Переключение между несколькими аккаунтами в одном браузере."""

from django.contrib.auth import login as auth_login

SESSION_KEY = 'kver_linked_account_ids'
MAX_LINKED_ACCOUNTS = 5


def _normalize_linked_ids(ids):
    """Уникальные ID в порядке добавления, не больше лимита."""
    normalized = list(dict.fromkeys(ids))
    if len(normalized) > MAX_LINKED_ACCOUNTS:
        normalized = normalized[-MAX_LINKED_ACCOUNTS:]
    return normalized


def save_linked_account_ids(request, ids):
    """Сохраняет список аккаунтов в сессии."""
    request.session[SESSION_KEY] = _normalize_linked_ids(ids)
    request.session.modified = True


def get_linked_account_ids(request):
    """ID аккаунтов, в которые входили на этом устройстве."""
    linked_ids = list(request.session.get(SESSION_KEY, []))
    if request.user.is_authenticated and request.user.pk not in linked_ids:
        linked_ids.append(request.user.pk)
        save_linked_account_ids(request, linked_ids)
    return linked_ids


def add_linked_account(request, user):
    """Добавляет аккаунт в список переключения."""
    linked_ids = list(request.session.get(SESSION_KEY, []))
    if request.user.is_authenticated and request.user.pk not in linked_ids:
        linked_ids.append(request.user.pk)
    if user.pk not in linked_ids:
        linked_ids.append(user.pk)
    save_linked_account_ids(request, linked_ids)


def remove_linked_account(request, user_id):
    """Убирает аккаунт из списка переключения."""
    linked_ids = get_linked_account_ids(request)
    if user_id in linked_ids:
        linked_ids.remove(user_id)
    save_linked_account_ids(request, linked_ids)
    return linked_ids


def clear_linked_accounts(request):
    """Полная очистка списка (выход из всех аккаунтов)."""
    request.session.pop(SESSION_KEY, None)
    request.session.modified = True


def get_linked_accounts(request):
    """Объекты пользователей в порядке добавления."""
    from .models import CustomUser

    ids = get_linked_account_ids(request)
    if not ids:
        return []

    users = CustomUser.objects.filter(pk__in=ids).select_related(
        'profile', 'organizer_profile', 'specialist_profile',
    )
    user_map = {user.pk: user for user in users}
    return [user_map[pk] for pk in ids if pk in user_map]


def switch_to_account(request, user):
    """Активирует выбранный аккаунт, сохраняя весь список переключения."""
    linked_ids = list(request.session.get(SESSION_KEY, []))
    if request.user.is_authenticated and request.user.pk not in linked_ids:
        linked_ids.append(request.user.pk)
    if user.pk not in linked_ids:
        linked_ids.append(user.pk)
    linked_ids = _normalize_linked_ids(linked_ids)

    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    # login() может сменить ключ сессии — список восстанавливаем явно
    request.session[SESSION_KEY] = linked_ids
    request.session.modified = True

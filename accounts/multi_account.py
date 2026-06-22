"""Переключение между несколькими аккаунтами в одном браузере."""

from django.contrib.auth import login as auth_login

SESSION_KEY = 'kver_linked_account_ids'
MAX_LINKED_ACCOUNTS = 5


def _coerce_account_id(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_linked_ids(ids):
    """Уникальные ID в порядке добавления, не больше лимита."""
    normalized = []
    for value in ids or []:
        account_id = _coerce_account_id(value)
        if account_id is not None:
            normalized.append(account_id)
    normalized = list(dict.fromkeys(normalized))
    if len(normalized) > MAX_LINKED_ACCOUNTS:
        normalized = normalized[-MAX_LINKED_ACCOUNTS:]
    return normalized


def save_linked_account_ids(request, ids):
    """Сохраняет список аккаунтов в сессии."""
    request.session[SESSION_KEY] = _normalize_linked_ids(ids)
    request.session.modified = True


def get_linked_account_ids(request):
    """ID аккаунтов, в которые входили на этом устройстве."""
    linked_ids = _normalize_linked_ids(request.session.get(SESSION_KEY, []))
    if request.user.is_authenticated:
        current_id = _coerce_account_id(request.user.pk)
        if current_id is not None and current_id not in linked_ids:
            linked_ids.append(current_id)
            save_linked_account_ids(request, linked_ids)
    return linked_ids


def add_linked_account(request, user):
    """Добавляет аккаунт в список переключения."""
    linked_ids = get_linked_account_ids(request) if request.user.is_authenticated else _normalize_linked_ids(
        request.session.get(SESSION_KEY, []),
    )
    account_id = _coerce_account_id(user.pk)
    if account_id is not None and account_id not in linked_ids:
        linked_ids.append(account_id)
    save_linked_account_ids(request, linked_ids)


def remove_linked_account(request, user_id):
    """Убирает аккаунт из списка переключения."""
    account_id = _coerce_account_id(user_id)
    linked_ids = get_linked_account_ids(request)
    if account_id is not None and account_id in linked_ids:
        linked_ids.remove(account_id)
    save_linked_account_ids(request, linked_ids)
    return linked_ids


def clear_linked_accounts(request):
    """Полная очистка списка (выход из всех аккаунтов)."""
    request.session.pop(SESSION_KEY, None)
    request.session.modified = True


def get_linked_accounts(request):
    """Объекты пользователей в порядке добавления."""
    from .models import CustomUser

    if not request.user.is_authenticated:
        return []

    ids = get_linked_account_ids(request)
    if not ids:
        return [request.user]

    users = CustomUser.objects.filter(pk__in=ids).select_related(
        'profile',
        'organizer_profile',
        'specialist_profile',
        'team_profile',
    )
    user_map = {user.pk: user for user in users}
    accounts = [user_map[pk] for pk in ids if pk in user_map]

    current_id = _coerce_account_id(request.user.pk)
    if current_id is not None and current_id not in user_map and request.user.pk not in {u.pk for u in accounts}:
        accounts.insert(0, request.user)

    return accounts


def switch_to_account(request, user):
    """Активирует выбранный аккаунт, сохраняя весь список переключения."""
    linked_ids = get_linked_account_ids(request)
    account_id = _coerce_account_id(user.pk)
    if account_id is not None and account_id not in linked_ids:
        linked_ids.append(account_id)
    linked_ids = _normalize_linked_ids(linked_ids)

    auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    # login() может сменить ключ сессии — список восстанавливаем явно
    request.session[SESSION_KEY] = linked_ids
    request.session.modified = True

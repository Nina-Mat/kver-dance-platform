"""Переключение и выход из отдельных аккаунтов."""

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .models import CustomUser
from .multi_account import (
    clear_linked_accounts,
    get_linked_account_ids,
    remove_linked_account,
    switch_to_account,
)


@login_required
def switch_account(request, pk):
    """Переключиться на другой сохранённый аккаунт."""
    linked_ids = get_linked_account_ids(request)
    if pk not in linked_ids:
        raise Http404

    user = get_object_or_404(CustomUser, pk=pk)
    switch_to_account(request, user)

    display = user.nickname or user.username
    messages.info(request, f'Вы переключились на @{display}')
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('core:feed')


@login_required
@require_POST
def remove_account(request, pk):
    """Выйти из одного аккаунта (убрать из списка переключения)."""
    linked_ids = get_linked_account_ids(request)
    if pk not in linked_ids:
        raise Http404

    user = get_object_or_404(CustomUser, pk=pk)
    display = user.nickname or user.username
    remaining = remove_linked_account(request, pk)

    if request.user.pk == pk:
        if remaining:
            next_user = get_object_or_404(CustomUser, pk=remaining[-1])
            switch_to_account(request, next_user)
            messages.info(
                request,
                f'Вы вышли из @{display}. Активен @{next_user.nickname or next_user.username}.',
            )
        else:
            logout(request)
            clear_linked_accounts(request)
            messages.info(request, f'Вы вышли из @{display}.')
            return redirect('core:landing')
    else:
        messages.info(request, f'Аккаунт @{display} удалён из списка.')

    return redirect('core:feed')

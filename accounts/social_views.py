"""Подписки, мессенджер и раздел фотокарточек."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from urllib.parse import urlparse

from .forms import PhotoAlbumForm, PhotoCardForm
from .models import (
    Conversation,
    CustomUser,
    Message,
    Notification,
    PhotoAlbum,
    PhotoCard,
    Subscription,
    Team,
    TeamMember,
)


def _redirect_back(request, fallback_name, **fallback_kwargs):
    """Возвращает на предыдущую страницу того же сайта."""
    referer = request.META.get('HTTP_REFERER')
    if referer:
        ref = urlparse(referer)
        site = urlparse(request.build_absolute_uri('/'))
        if ref.netloc == site.netloc:
            return redirect(referer)
    return redirect(fallback_name, **fallback_kwargs)


def get_profile_social_context(request, profile_user):
    """Контекст подписок для страницы профиля."""
    is_subscribed = False
    if request.user.is_authenticated and not (request.user == profile_user):
        is_subscribed = profile_user.is_subscribed_by(request.user)
    return {
        'is_subscribed': is_subscribed,
        'subscribers_count': profile_user.subscribers_count,
    }


@login_required
@require_POST
def subscribe(request, pk):
    """Подписаться на профиль."""
    target = get_object_or_404(CustomUser, pk=pk)
    if request.user == target:
        messages.error(request, 'Нельзя подписаться на самого себя.')
        return _redirect_back(request, 'accounts:profile', pk=pk)

    _, created = Subscription.objects.get_or_create(
        subscriber=request.user,
        target=target,
    )
    if created:
        messages.success(request, f'Вы подписались на @{target.nickname or target.username}.')
    return _redirect_back(request, 'accounts:profile', pk=pk)


@login_required
@require_POST
def unsubscribe(request, pk):
    """Отписаться от профиля."""
    target = get_object_or_404(CustomUser, pk=pk)
    Subscription.objects.filter(subscriber=request.user, target=target).delete()
    messages.info(request, 'Подписка отменена.')
    return _redirect_back(request, 'accounts:profile', pk=pk)


@login_required
def notification_read(request, pk):
    """Открыть уведомление и пометить прочитанным."""
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user,
    )
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
    return redirect(notification.get_target_url())


@login_required
@require_GET
def subscription_suggest(request):
    """Подсказки из подписок для добавления участника в команду."""
    q = (request.GET.get('q') or '').strip().lstrip('@')
    team_id = request.GET.get('team_id')

    subs = Subscription.objects.filter(
        subscriber=request.user,
    ).select_related('target').exclude(target__user_type='team')

    if team_id:
        member_ids = TeamMember.objects.filter(
            team_id=team_id,
        ).values_list('user_id', flat=True)
        subs = subs.exclude(target_id__in=member_ids)
        try:
            team = Team.objects.get(pk=team_id)
            subs = subs.exclude(target_id=team.leader_id)
        except Team.DoesNotExist:
            pass

    if q:
        subs = subs.filter(
            Q(target__nickname__icontains=q) | Q(target__username__icontains=q),
        )

    results = []
    for sub in subs[:15]:
        user = sub.target
        nickname = user.nickname or user.username
        results.append({
            'username': user.username,
            'nickname': nickname,
            'label': f'@{nickname}',
        })

    return JsonResponse({'results': results})


@login_required
def subscriptions_list(request):
    """Список профилей, на которые подписан пользователь."""
    subs = Subscription.objects.filter(
        subscriber=request.user,
    ).select_related('target').order_by('-created_at')

    paginator = Paginator(subs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'accounts/subscriptions.html', {
        'page_obj': page_obj,
        'subscriptions': page_obj,
    })


@login_required
def messenger_list(request):
    """Список диалогов."""
    conversations = Conversation.objects.filter(
        Q(participant1=request.user) | Q(participant2=request.user),
    ).select_related('participant1', 'participant2').order_by('-updated_at')

    dialog_items = []
    for conv in conversations:
        other = conv.other_participant(request.user)
        last = conv.last_message()
        unread = conv.messages.filter(is_read=False).exclude(sender=request.user).count()
        dialog_items.append({
            'conversation': conv,
            'other_user': other,
            'last_message': last,
            'unread_count': unread,
        })

    return render(request, 'accounts/messenger.html', {
        'dialog_items': dialog_items,
    })


@login_required
def chat_detail(request, pk):
    """Переписка с пользователем."""
    other_user = get_object_or_404(CustomUser, pk=pk)
    if other_user == request.user:
        raise Http404

    conversation = Conversation.get_or_create_for_users(request.user, other_user)

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                text=text,
            )
            conversation.save()
        return redirect('accounts:chat', pk=other_user.pk)

    chat_messages = conversation.messages.select_related('sender').order_by('created_at')
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    return render(request, 'accounts/chat.html', {
        'other_user': other_user,
        'conversation': conversation,
        'chat_messages': chat_messages,
    })


@login_required
def photos_section(request):
    """Раздел фотокарточек: мои фото, отметки, альбомы."""
    tab = request.GET.get('tab', 'mine')
    user = request.user

    my_photos = PhotoCard.objects.filter(user=user).select_related(
        'album', 'linked_event', 'linked_cover',
    ).prefetch_related('tagged_users').order_by('-created_at')

    tagged_photos = PhotoCard.objects.filter(
        tagged_users=user,
    ).exclude(user=user).select_related(
        'user', 'album',
    ).prefetch_related('tagged_users').order_by('-created_at')

    albums = PhotoAlbum.objects.filter(user=user).prefetch_related('photos').order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_album':
            form = PhotoAlbumForm(request.POST)
            if form.is_valid():
                album = form.save(commit=False)
                album.user = user
                album.save()
                messages.success(request, f'Альбом «{album.title}» создан.')
                return redirect(f"{request.path}?tab=albums")
        elif action == 'upload_photo':
            form = PhotoCardForm(request.POST, request.FILES, user=user)
            if form.is_valid():
                card = form.save(commit=False)
                card.user = user
                card.save()
                messages.success(request, 'Фото добавлено.')
                return redirect(f"{request.path}?tab=mine")

    album_form = PhotoAlbumForm()
    photocard_form = PhotoCardForm(user=user)
    if user.photo_albums.exists():
        photocard_form.fields['album'].queryset = user.photo_albums.all()

    return render(request, 'accounts/photos_section.html', {
        'tab': tab,
        'my_photos': my_photos,
        'tagged_photos': tagged_photos,
        'albums': albums,
        'album_form': album_form,
        'photocard_form': photocard_form,
    })

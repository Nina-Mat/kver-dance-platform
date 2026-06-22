from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import CreateView, DetailView, ListView, TemplateView, UpdateView
from django.http import Http404

from core.feed_utils import build_covers_feed, build_performances_feed

from .forms import CommentForm, CoverMediaForm
from .models import CoverMedia, Comment, CoverLike, CommentLike
from .moderation import MODERATION_POLICY_MESSAGE
from .utils import fetch_youtube_metadata, parse_youtube_url, record_cover_view, resolve_mentioned_users


def user_can_manage_cover(user, cover):
    """Редактировать или удалить публикацию может автор или администрация."""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return cover.author_id == user.pk


def _save_cover_from_form(form, instance):
    """Применяет данные формы к публикации (создание и редактирование)."""
    source_type = form.cleaned_data.get('source_type')

    if source_type == 'youtube':
        video_id = form.cleaned_data['youtube_id']
        instance.source_type = 'youtube'
        instance.youtube_id = video_id
        instance.youtube_url = form.cleaned_data['youtube_url']
        instance.video_file = None

        metadata = fetch_youtube_metadata(video_id)
        if metadata:
            if not (instance.title or '').strip():
                instance.title = metadata.get('title') or f'YouTube {video_id}'
            instance.thumbnail_url = metadata.get('thumbnail_url') or instance.thumbnail_url
            if not (instance.description or '').strip() and metadata.get('description'):
                instance.description = metadata['description']
            instance.duration = metadata.get('duration') or instance.duration
            instance.youtube_views = metadata.get('youtube_views') or 0
            instance.youtube_likes = metadata.get('youtube_likes') or 0
        if not (instance.title or '').strip():
            instance.title = f'YouTube {video_id}'
    else:
        instance.source_type = 'upload'
        instance.youtube_id = ''
        instance.youtube_url = ''

    return instance


class CoverMediaCreateView(LoginRequiredMixin, CreateView):
    """Создание публикации: YouTube или локальный файл."""

    model = CoverMedia
    form_class = CoverMediaForm
    template_name = 'media_app/upload.html'
    success_url = reverse_lazy('core:feed')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.is_approved = True
        _save_cover_from_form(form, form.instance)

        response = super().form_valid(form)
        mentioned_users = resolve_mentioned_users(
            self.object.description,
            self.object.tags,
        )
        self.object.mentioned_users.set(mentioned_users)
        messages.success(self.request, 'Публикация добавлена в ленту.')
        return response

    def form_invalid(self, form):
        for error in form.non_field_errors():
            tags = 'moderation error' if str(error) == MODERATION_POLICY_MESSAGE else 'error'
            messages.error(self.request, error, extra_tags=tags)
        for field_name, errors in form.errors.items():
            if field_name == '__all__':
                continue
            for error in errors:
                label = form.fields.get(field_name).label if field_name in form.fields else field_name
                tags = 'moderation error' if str(error) == MODERATION_POLICY_MESSAGE else 'error'
                messages.error(self.request, f'{label}: {error}', extra_tags=tags)
        return super().form_invalid(form)


class CoverMediaUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование публикации (автор или администрация)."""

    model = CoverMedia
    form_class = CoverMediaForm
    template_name = 'media_app/upload.html'

    def get_object(self, queryset=None):
        cover = get_object_or_404(CoverMedia, pk=self.kwargs['pk'])
        if not user_can_manage_cover(self.request.user, cover):
            raise Http404
        return cover

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        if self.object.youtube_url:
            initial['youtube_url'] = self.object.youtube_url
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        _save_cover_from_form(form, form.instance)
        response = super().form_valid(form)
        mentioned_users = resolve_mentioned_users(
            self.object.description,
            self.object.tags,
        )
        self.object.mentioned_users.set(mentioned_users)
        messages.success(self.request, 'Публикация обновлена.')
        return response

    def get_success_url(self):
        return reverse('media_app:detail', kwargs={'pk': self.object.pk})


class CoverMediaFeedView(ListView):
    """Лента одобренных публикаций."""

    model = CoverMedia
    template_name = 'media_app/feed.html'
    context_object_name = 'covers'
    paginate_by = 6

    def get_queryset(self):
        return CoverMedia.objects.filter(
            is_approved=True,
        ).select_related('author').prefetch_related(
            'mentioned_users',
        ).order_by('-created_at')


class CoverMediaDetailView(DetailView):
    """Страница публикации."""

    model = CoverMedia
    template_name = 'media_app/detail.html'
    context_object_name = 'cover'

    def get_queryset(self):
        return CoverMedia.objects.select_related('author').prefetch_related(
            'mentioned_users',
            'comments__user',
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        record_cover_view(request, self.object)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        comments = (
            self.object.comments.filter(is_approved=True)
            .select_related('user', 'user__profile')
            .annotate(likes_count=Count('likes'))
            .order_by('created_at')
        )
        context['comments'] = comments
        context['comments_count'] = comments.count()
        user = self.request.user
        context['user_liked'] = False
        context['user_liked_comment_ids'] = set()
        if user.is_authenticated:
            context['user_liked'] = CoverLike.objects.filter(
                user=user, media=self.object,
            ).exists()
            context['user_liked_comment_ids'] = set(
                CommentLike.objects.filter(
                    user=user,
                    comment__in=comments,
                ).values_list('comment_id', flat=True)
            )
        context['likes_count'] = self.object.likes.count()
        context['can_manage_cover'] = user_can_manage_cover(self.request.user, self.object)
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    """Добавление комментария к публикации."""

    model = Comment
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.media = CoverMedia.objects.get(pk=self.kwargs['pk'])
        form.instance.is_approved = True
        messages.success(self.request, 'Комментарий опубликован.')
        return super().form_valid(form)

    def form_invalid(self, form):
        for field_errors in form.errors.values():
            for error in field_errors:
                tags = 'moderation error' if str(error) == MODERATION_POLICY_MESSAGE else 'error'
                messages.error(self.request, error, extra_tags=tags)
        return redirect('media_app:detail', pk=self.kwargs['pk'])

    def get_success_url(self):
        return reverse_lazy('media_app:detail', kwargs={'pk': self.kwargs['pk']})

@require_GET
def youtube_preview(request):
    """AJAX-превью YouTube по ссылке (YouTube Data API v3 + fallback)."""
    url = request.GET.get('url', '').strip()
    video_id = parse_youtube_url(url)
    if not video_id:
        return JsonResponse({'error': 'invalid_url'}, status=400)

    metadata = fetch_youtube_metadata(video_id)
    return JsonResponse({
        'video_id': video_id,
        **metadata,
    })


@login_required
@require_POST
def delete_cover(request, pk):
    """Удаление публикации автором или администрацией."""
    cover = get_object_or_404(CoverMedia, pk=pk)
    if not user_can_manage_cover(request.user, cover):
        messages.error(request, 'Нет прав для удаления этой публикации.')
        return redirect('media_app:detail', pk=pk)

    cover.delete()
    messages.success(request, 'Публикация удалена.')
    return redirect('core:feed')


@login_required
@require_POST
def toggle_like(request, pk):
    """Поставить или убрать лайк с публикации."""
    cover = get_object_or_404(CoverMedia, pk=pk, is_approved=True)
    like, created = CoverLike.objects.get_or_create(user=request.user, media=cover)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    count = cover.likes.count()
    cover.likes_kver = count
    cover.save(update_fields=['likes_kver'])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'likes_count': count})
    return redirect('media_app:detail', pk=pk)


@login_required
@require_POST
def toggle_comment_like(request, pk, comment_pk):
    """Поставить или убрать лайк с комментария."""
    comment = get_object_or_404(
        Comment,
        pk=comment_pk,
        media_id=pk,
        is_approved=True,
    )
    like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
    if not created:
        like.delete()
    return redirect('media_app:detail', pk=pk)


def user_can_delete_comment(user, comment, cover):
    """Удалять комментарий может его автор или владелец поста."""
    if not user.is_authenticated:
        return False
    if comment.user_id == user.pk:
        return True
    return cover.author_id == user.pk


@login_required
@require_POST
def delete_comment(request, pk, comment_pk):
    """Удаление комментария автором или владельцем поста."""
    cover = get_object_or_404(CoverMedia, pk=pk)
    comment = get_object_or_404(
        Comment,
        pk=comment_pk,
        media=cover,
        is_approved=True,
    )

    if not user_can_delete_comment(request.user, comment, cover):
        messages.error(request, 'Нет прав для удаления этого комментария.')
        return redirect('media_app:detail', pk=pk)

    comment.delete()
    messages.success(request, 'Комментарий удалён.')
    return redirect(f"{reverse('media_app:detail', kwargs={'pk': pk})}#comments")


class CoversFeedView(LoginRequiredMixin, TemplateView):
    """Рекомендации каверов (YouTube)."""

    template_name = 'media_app/covers_feed.html'
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['covers'] = build_covers_feed(limit=30)
        return context


class PerformancesFeedView(LoginRequiredMixin, TemplateView):
    """Рекомендации выступлений (загруженные видео)."""

    template_name = 'media_app/performances_feed.html'
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['performances'] = build_performances_feed(limit=30)
        return context

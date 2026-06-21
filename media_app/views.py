from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_GET
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from core.feed_utils import build_covers_feed, build_performances_feed

from .forms import CommentForm, CoverMediaForm
from .models import CoverMedia, Comment
from .utils import fetch_youtube_metadata, parse_youtube_url, resolve_mentioned_users

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
        source_type = form.cleaned_data.get('source_type')

        if source_type == 'youtube':
            video_id = form.cleaned_data['youtube_id']
            form.instance.source_type = 'youtube'
            form.instance.youtube_id = video_id
            form.instance.youtube_url = form.cleaned_data['youtube_url']
            form.instance.video_file = None

            metadata = fetch_youtube_metadata(video_id)
            if metadata:
                if not form.instance.title:
                    form.instance.title = metadata['title'] or form.instance.title
                form.instance.thumbnail_url = metadata['thumbnail_url']
                if not form.instance.description:
                    form.instance.description = metadata['description']
                form.instance.duration = metadata['duration']
                form.instance.youtube_views = metadata['youtube_views']
                form.instance.youtube_likes = metadata['youtube_likes']
        else:
            form.instance.source_type = 'upload'
            form.instance.youtube_id = ''
            form.instance.youtube_url = ''

        response = super().form_valid(form)
        mentioned_users = resolve_mentioned_users(
            self.object.description,
            self.object.tags,
        )
        self.object.mentioned_users.set(mentioned_users)
        return response


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        context['comments'] = self.object.comments.filter(is_approved=True)
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
                messages.error(self.request, error)
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

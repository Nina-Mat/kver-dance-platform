from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.decorators.http import require_GET
from urllib.parse import quote

from core.feed_utils import build_feed_items
from core.search import global_search, CATEGORY_LABELS


class LandingView(TemplateView):
    template_name = 'core/landing.html'


class FeedView(LoginRequiredMixin, TemplateView):
    """Гибридная лента: фотокарточки, каверы и выступления."""

    template_name = 'core/feed.html'
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_items = build_feed_items(self.request.user, limit=200)
        paginator = Paginator(all_items, 10)
        page_obj = paginator.get_page(self.request.GET.get('page'))
        context['feed_items'] = page_obj
        context['page_obj'] = page_obj
        return context


class TeamsView(LoginRequiredMixin, TemplateView):
    template_name = 'core/teams.html'
    login_url = '/accounts/login/'


class SpecialistsView(LoginRequiredMixin, TemplateView):
    template_name = 'core/specialists.html'
    login_url = '/accounts/login/'


class SearchView(TemplateView):
    """Страница результатов глобального поиска."""

    template_name = 'core/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        context['query'] = query
        context['category_labels'] = CATEGORY_LABELS

        if len(query) >= 2:
            context['results'] = global_search(query, limits={
                'users': 20,
                'teams': 15,
                'covers': 20,
                'performances': 20,
                'photos': 20,
                'events': 15,
            })
            total = sum(len(v) for v in context['results'].values())
            context['total_count'] = total
        else:
            context['results'] = {}
            context['total_count'] = 0

        return context


@require_GET
def search_suggest(request):
    """AJAX-подсказки при вводе в строку поиска."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'results': [], 'query': query})

    grouped = global_search(query, limits={
        'users': 4,
        'teams': 3,
        'covers': 3,
        'performances': 3,
        'photos': 3,
        'events': 3,
    })

    from core.search import results_to_json
    results = results_to_json(grouped)
    total = len(results)

    return JsonResponse({
        'query': query,
        'results': results,
        'total': total,
        'search_url': f"{reverse('core:search')}?q={quote(query)}",
    })

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import TemplateView
from django.views.decorators.http import require_GET, require_POST

from core.feed_utils import build_feed_items
from core.forms import InfoPostForm
from core.models import InfoPost
from core.search import global_search, CATEGORY_LABELS
from core.utils import get_kver_admin_user


FAQ_ITEMS = [
    {
        'question': 'Как зарегистрироваться и настроить профиль?',
        'answer': (
            'Создайте аккаунт, выберите тип профиля и заполните @username, '
            'фото и описание. Ник отображается в ссылке на ваш профиль.'
        ),
    },
    {
        'question': 'Как опубликовать кавер или выступление?',
        'answer': (
            'Перейдите в раздел публикации, выберите YouTube-ссылку или загрузку файла, '
            'укажите тип «Кавер» или «Выступление» и нажмите «Опубликовать».'
        ),
    },
    {
        'question': 'Как подписаться на пользователя и что даёт подписка?',
        'answer': (
            'На странице профиля нажмите «Подписаться». Контент подписок чаще '
            'появляется в вашей ленте.'
        ),
    },
    {
        'question': 'Как подать заявку в команду или на мероприятие?',
        'answer': (
            'Для команды откройте профиль с открытым набором и нажмите «Подать заявку». '
            'Для мероприятия — кнопку «Подать заявку» на странице события до дедлайна.'
        ),
    },
    {
        'question': 'Почему не публикуется комментарий или пост?',
        'answer': (
            'Платформа блокирует нецензурную лексику и запрещённые слова. '
            'Исправьте текст и попробуйте снова.'
        ),
    },
    {
        'question': 'Как связаться с администрацией?',
        'answer': (
            'Используйте кнопку «Связаться с администратором» на этой странице '
            'или профиль «Администрация KVER» — напишите о проблеме в личные сообщения.'
        ),
    },
]

COMMUNITY_RULES = [
    'Уважайте участников: без оскорблений, травли и дискриминации.',
    'Не публикуйте спам, мошеннические ссылки и чужой контент без разрешения.',
    'Запрещена нецензурная лексика в постах, комментариях и профиле.',
    'Каверы и выступления должны соответствовать тематике cover dance.',
    'Заявки в команды и на мероприятия подавайте честно — ложные данные могут привести к блокировке.',
    'Администрация вправе удалить контент, нарушающий правила платформы.',
]


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

    def get_context_data(self, **kwargs):
        from accounts.models import Team
        context = super().get_context_data(**kwargs)
        context['teams'] = Team.objects.select_related('leader').order_by('-created_at')[:50]
        return context


class HelpView(TemplateView):
    template_name = 'core/help.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        admin_user = get_kver_admin_user()
        context['faq_items'] = FAQ_ITEMS
        context['community_rules'] = COMMUNITY_RULES
        context['kver_admin_user'] = admin_user
        if admin_user:
            context['admin_chat_url'] = reverse('accounts:chat', kwargs={'pk': admin_user.pk})
        return context


def _require_superuser(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        messages.error(request, 'Доступ только для администрации KVER.')
        return False
    return True


@login_required
@require_POST
def info_post_create(request):
    if not _require_superuser(request):
        return redirect('core:help')

    form = InfoPostForm(request.POST)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        messages.success(request, 'Информационный пост опубликован.')
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)

    return redirect('accounts:profile', pk=request.user.pk)


@login_required
@require_POST
def info_post_edit(request, pk):
    if not _require_superuser(request):
        return redirect('core:help')

    post = get_object_or_404(InfoPost, pk=pk)
    form = InfoPostForm(request.POST, instance=post)
    if form.is_valid():
        form.save()
        messages.success(request, 'Пост обновлён.')
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)

    return redirect('accounts:profile', pk=request.user.pk)


@login_required
@require_POST
def info_post_delete(request, pk):
    if not _require_superuser(request):
        return redirect('core:help')

    post = get_object_or_404(InfoPost, pk=pk)
    post.delete()
    messages.success(request, 'Информационный пост удалён.')
    return redirect('accounts:profile', pk=request.user.pk)


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
    from urllib.parse import quote

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

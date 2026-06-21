from django.shortcuts import render, get_object_or_404, redirect

from django.views.generic import View

from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.forms import AuthenticationForm

from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.core.exceptions import ValidationError

from django.db import IntegrityError

from django.db.models import Prefetch

from django.urls import reverse

from django.http import Http404

from django.views.decorators.http import require_POST



from .models import CustomUser, Team, TeamMember, TeamApplication, UserProfile, OrganizerProfile, SpecialistProfile, PhotoCard

from .notifications import create_notification

from .social_views import get_profile_social_context

from .forms import (

    TeamProfileForm,

    SoloProfileEditForm,

    UserProfileForm,

    CustomUserForm,

    OrganizerProfileForm,

    SpecialistProfileForm,

    PhotoCardForm,

    TeamMemberAddForm,

    TeamApplicationForm,

    normalize_nickname,

    validate_unique_nickname,

    validate_unique_team_username,

)

from media_app.models import CoverMedia

from events.models import Event, EventApplication

from .social_views import get_profile_social_context
from .multi_account import (
    add_linked_account,
    clear_linked_accounts,
    get_linked_account_ids,
    save_linked_account_ids,
    SESSION_KEY,
)





def get_user_cover_style(user):

    """Возвращает CSS-градиент обложки пользователя с учётом типа аккаунта."""

    if user.user_type == 'solo':

        profile = getattr(user, 'profile', None)

        if profile:

            return profile.get_cover_gradient_style()

    return user.get_cover_gradient_style()





def resolve_login_username(identifier):

    """Находит username для входа по логину или @nickname."""

    identifier = normalize_nickname(identifier)

    if not identifier:

        return identifier



    user = CustomUser.objects.filter(username__iexact=identifier).first()

    if user:

        return user.username



    user = CustomUser.objects.filter(nickname__iexact=identifier).first()

    if user:

        return user.username



    return identifier





# ==========================================

# АУТЕНТИФИКАЦИЯ

# ==========================================



class CustomLoginView(View):

    """Вход в систему."""



    def get(self, request):

        add_account = request.GET.get('add') == '1'

        if request.user.is_authenticated and not add_account:

            return redirect('core:feed')

        form = AuthenticationForm()

        return render(request, 'accounts/login.html', {
            'form': form,
            'add_account': add_account,
        })



    def post(self, request):

        identifier = request.POST.get('username', '')

        password = request.POST.get('password')

        username = resolve_login_username(identifier)

        user = authenticate(request, username=username, password=password)



        if user is not None:

            display_name = user.nickname or user.username
            is_add_account = request.POST.get('add_account') == '1'

            if is_add_account and request.user.is_authenticated:
                if user.pk == request.user.pk:
                    messages.info(request, 'Этот аккаунт уже активен.')
                elif user.pk in get_linked_account_ids(request):
                    messages.info(request, f'@{display_name} уже есть в списке аккаунтов.')
                else:
                    add_linked_account(request, user)
                    messages.success(
                        request,
                        f'Аккаунт @{display_name} добавлен. Вы по-прежнему в @{request.user.nickname or request.user.username}.',
                    )
                return redirect('core:feed')

            login(request, user)

            linked_ids = list(request.session.get(SESSION_KEY, []))
            if user.pk not in linked_ids:
                linked_ids.append(user.pk)
            save_linked_account_ids(request, linked_ids)
            messages.success(request, f'Добро пожаловать, @{display_name}!')
            return redirect('core:feed')



        messages.error(request, 'Неверное имя пользователя или пароль.')

        form = AuthenticationForm()

        return render(request, 'accounts/login.html', {
            'form': form,
            'add_account': request.GET.get('add') == '1' or request.POST.get('add_account') == '1',
        })





class CustomLogoutView(View):

    """Выход из системы."""



    def get(self, request):

        clear_linked_accounts(request)

        logout(request)

        messages.info(request, 'Вы вышли из системы.')

        return redirect('core:landing')





class RegisterView(View):

    """Регистрация с выбором типа аккаунта."""



    def get(self, request):

        if request.user.is_authenticated:

            return redirect('core:feed')

        return render(request, 'accounts/register.html')



    def post(self, request):

        username = request.POST.get('username', '').strip()

        nickname = normalize_nickname(request.POST.get('nickname', ''))

        team_username = normalize_nickname(request.POST.get('team_username', ''))

        team_name = request.POST.get('team_name', '').strip()

        email = request.POST.get('email', '').strip()

        password1 = request.POST.get('password1')

        password2 = request.POST.get('password2')

        user_type = request.POST.get('user_type')



        if password1 != password2:

            messages.error(request, 'Пароли не совпадают!')

            return render(request, 'accounts/register.html')



        if CustomUser.objects.filter(username=username).exists():

            messages.error(request, 'Пользователь с таким именем уже существует!')

            return render(request, 'accounts/register.html')



        if user_type == 'team':

            if not team_username:

                messages.error(request, 'Укажите уникальное @username команды.')

                return render(request, 'accounts/register.html')

            try:

                validate_unique_team_username(team_username)

            except ValidationError as exc:

                messages.error(request, exc.messages[0])

                return render(request, 'accounts/register.html')

            if not team_name:

                messages.error(request, 'Укажите название команды.')

                return render(request, 'accounts/register.html')

        else:

            if not nickname:

                messages.error(request, 'Уникальное @username обязательно для заполнения.')

                return render(request, 'accounts/register.html')

            try:

                validate_unique_nickname(nickname)

            except ValidationError as exc:

                messages.error(request, exc.messages[0])

                return render(request, 'accounts/register.html')



        user = CustomUser.objects.create_user(

            username=username,

            email=email,

            password=password1,

            user_type=user_type,

            nickname=nickname if user_type != 'team' else None,

        )



        if user_type == 'solo':

            UserProfile.objects.create(user=user)

        elif user_type == 'organizer':

            OrganizerProfile.objects.create(user=user)

        elif user_type == 'specialist':

            SpecialistProfile.objects.create(user=user, specialization='other')

        elif user_type == 'team':

            Team.objects.create(

                leader=user,

                name=team_name,

                username=team_username,

            )



        messages.success(request, 'Аккаунт создан! Теперь войдите.')

        return redirect('accounts:login')





# ==========================================

# ПРОФИЛИ

# ==========================================



class ProfileView(View):

    """Универсальный просмотр профиля любого типа (кроме команд)."""



    def get(self, request, pk):

        profile_user = get_object_or_404(

            CustomUser.objects.select_related(

                'profile', 'organizer_profile', 'specialist_profile', 'team_profile'

            ),

            pk=pk,

        )

        user_type = profile_user.user_type



        context = {

            'profile_user': profile_user,

            'is_owner': request.user.is_authenticated and request.user == profile_user,

            'cover_style': get_user_cover_style(profile_user),

        }

        context.update(get_profile_social_context(request, profile_user))



        if user_type == 'team':

            try:

                team = profile_user.team_profile

                return redirect('accounts:team_profile', pk=team.pk)

            except Team.DoesNotExist:

                messages.warning(request, 'Профиль команды ещё не создан.')

                return redirect('core:landing')



        elif user_type == 'solo':

            UserProfile.objects.get_or_create(user=profile_user)



            user_teams = Team.objects.filter(

                team_memberships__user=profile_user

            ).distinct()



            videos_qs = CoverMedia.objects.filter(

                author=profile_user,

                is_approved=True,

            ).order_by('-created_at')



            mentioned_qs = CoverMedia.objects.filter(

                mentioned_users=profile_user,

                is_approved=True,

            ).exclude(

                author=profile_user,

            ).distinct().order_by('-created_at')



            photo_cards = PhotoCard.objects.filter(

                user=profile_user,

            ).select_related('linked_event', 'linked_cover').order_by('-created_at')



            photocard_form = None

            if context['is_owner']:

                photocard_form = PhotoCardForm(user=profile_user)



            context.update({

                'user_teams': user_teams,

                'user_videos': videos_qs,

                'user_covers': mentioned_qs,

                'user_performances': CoverMedia.objects.filter(

                    author=profile_user,

                    is_approved=True,

                    source_type='upload',

                ).order_by('-created_at'),

                'photo_cards': photo_cards,

                'photocard_form': photocard_form,

                'upload_url': reverse('media_app:upload'),

            })

            return render(request, 'accounts/solo_profile.html', context)



        elif user_type == 'organizer':

            organizer_events = Event.objects.filter(

                organizer=profile_user,

            ).order_by('-event_date')



            applications_qs = EventApplication.objects.filter(

                event__organizer=profile_user,

            ).select_related('event', 'applicant').order_by('-created_at')



            status_filter = request.GET.get('status', '')

            if status_filter in dict(EventApplication.STATUS_CHOICES):

                applications_qs = applications_qs.filter(status=status_filter)



            context.update({

                'organizer_events': organizer_events,

                'organizer_applications': applications_qs,

                'application_status_filter': status_filter,

                'application_status_choices': EventApplication.STATUS_CHOICES,

                'events_count': organizer_events.count(),

                'participants_count': EventApplication.objects.filter(

                    event__organizer=profile_user,

                    status='approved',

                ).count(),

                'rating': None,

            })

            return render(request, 'accounts/organizer_profile.html', context)



        elif user_type == 'specialist':

            context.update({

                'works_count': 0,

                'orders_count': 0,

                'rating': '5.0',

            })

            return render(request, 'accounts/specialist_profile.html', context)



        return redirect('core:landing')





class ProfileEditView(View):

    """Редактирование профиля пользователя с учётом типа аккаунта."""



    template_name = 'accounts/profile_edit.html'



    def dispatch(self, request, *args, **kwargs):

        if not request.user.is_authenticated:

            return redirect('accounts:login')

        return super().dispatch(request, *args, **kwargs)



    def get_profile_user(self, pk):

        """Возвращает редактируемого пользователя или вызывает 404."""

        profile_user = get_object_or_404(

            CustomUser.objects.select_related(

                'profile', 'organizer_profile', 'specialist_profile', 'team_profile'

            ),

            pk=pk,

        )

        if self.request.user.pk != profile_user.pk:

            messages.error(self.request, 'Вы не можете редактировать этот профиль.')

            raise Http404

        return profile_user



    def get_extra_social_links(self, profile):

        """Возвращает дополнительные соцсети (кроме VK и Telegram)."""

        if not profile or not profile.social_links:

            return []

        reserved = {'vk', 'telegram'}

        return [

            {'name': name, 'url': url}

            for name, url in profile.social_links.items()

            if name.lower() not in reserved

        ]



    def get_forms(self, profile_user, data=None, files=None):

        """Создаёт набор форм в зависимости от типа аккаунта."""

        user_type = profile_user.user_type

        kwargs = {'data': data, 'files': files}



        if user_type == 'solo':

            profile, _ = UserProfile.objects.get_or_create(user=profile_user)

            return {

                'user_form': SoloProfileEditForm(**kwargs, instance=profile_user),

                'profile_form': UserProfileForm(**kwargs, instance=profile),

                'extra_social_links': self.get_extra_social_links(profile),

                'user_type': user_type,

            }



        if user_type == 'organizer':

            organizer_profile, _ = OrganizerProfile.objects.get_or_create(user=profile_user)

            return {

                'user_form': CustomUserForm(**kwargs, instance=profile_user),

                'type_form': OrganizerProfileForm(**kwargs, instance=organizer_profile),

                'user_type': user_type,

            }



        if user_type == 'specialist':

            specialist_profile, _ = SpecialistProfile.objects.get_or_create(user=profile_user)

            return {

                'user_form': CustomUserForm(**kwargs, instance=profile_user),

                'type_form': SpecialistProfileForm(**kwargs, instance=specialist_profile),

                'user_type': user_type,

            }



        return {'user_type': user_type}



    def get(self, request, pk):

        profile_user = self.get_profile_user(pk)



        if profile_user.user_type == 'team':

            try:

                return redirect('accounts:team_edit', pk=profile_user.team_profile.pk)

            except Team.DoesNotExist:

                messages.warning(request, 'Сначала создайте профиль команды.')

                return redirect('accounts:profile', pk=profile_user.pk)



        context = {

            'profile_user': profile_user,

            **self.get_forms(profile_user),

        }

        return render(request, self.template_name, context)



    def post(self, request, pk):

        profile_user = self.get_profile_user(pk)



        if profile_user.user_type == 'team':

            try:

                return redirect('accounts:team_edit', pk=profile_user.team_profile.pk)

            except Team.DoesNotExist:

                raise Http404



        forms = self.get_forms(profile_user, data=request.POST, files=request.FILES)

        user_type = forms.pop('user_type')

        extra_social_links = forms.pop('extra_social_links', [])

        user_form = forms['user_form']



        if user_type == 'solo':

            profile_form = forms['profile_form']

            if user_form.is_valid() and profile_form.is_valid():

                user_form.save()

                profile_form.save()

                messages.success(request, 'Профиль успешно обновлён!')

                return redirect('accounts:profile', pk=profile_user.pk)

        else:

            type_form = forms['type_form']

            if user_form.is_valid() and type_form.is_valid():

                user_form.save()

                type_form.save()

                messages.success(request, 'Профиль успешно обновлён!')

                return redirect('accounts:profile', pk=profile_user.pk)



        context = {

            'profile_user': profile_user,

            'user_type': user_type,

            'extra_social_links': extra_social_links,

            'user_form': user_form,

            **forms,

        }

        return render(request, self.template_name, context)





# ==========================================

# КОМАНДЫ

# ==========================================



def team_profile(request, pk):

    """Профиль команды (публичный доступ)."""

    team = get_object_or_404(

        Team.objects.select_related('leader').prefetch_related(

            Prefetch(

                'team_memberships',

                queryset=TeamMember.objects.select_related('user', 'user__profile'),

            )

        ),

        pk=pk,

    )



    members = team.team_memberships.all()

    team_videos = CoverMedia.objects.filter(

        team=team,

        is_approved=True,

    ).order_by('-created_at')



    is_owner = request.user.is_authenticated and request.user == team.leader

    add_member_form = None
    members_slots_remaining = None
    if is_owner:
        add_member_form = TeamMemberAddForm(team)
        members_slots_remaining = max(0, team.max_members - team.members_count())

    profile_user = team.leader
    social_ctx = get_profile_social_context(request, profile_user)

    is_team_member = False
    has_pending_application = False
    if request.user.is_authenticated:
        is_team_member = TeamMember.objects.filter(team=team, user=request.user).exists()
        has_pending_application = TeamApplication.objects.filter(
            team=team,
            applicant=request.user,
            status='pending',
        ).exists()

    context = {

        'team': team,

        'members': members,

        'is_owner': is_owner,

        'profile_user': profile_user,

        'is_team_member': is_team_member,

        'has_pending_application': has_pending_application,

        'add_member_form': add_member_form,

        'members_slots_remaining': members_slots_remaining,

        'members_count': team.members_count(),

        'performances_count': team_videos.count(),

        'team_videos': team_videos,

        'team_performances': CoverMedia.objects.filter(
            team=team,
            is_approved=True,
            source_type='upload',
        ).order_by('-created_at'),

        'cover_style': team.get_cover_gradient_style(),

    }

    context.update(social_ctx)

    return render(request, 'accounts/team_profile.html', context)


def _team_members_tab_url(team_pk):
    return reverse('accounts:team_profile', kwargs={'pk': team_pk}) + '#members'


@login_required
def team_add_member(request, pk):
    """Добавление участника в команду (только лидер)."""
    team = get_object_or_404(Team, pk=pk)
    if request.user != team.leader:
        messages.error(request, 'Только лидер может добавлять участников.')
        return redirect('accounts:team_profile', pk=pk)
    if request.method != 'POST':
        return redirect(_team_members_tab_url(pk))

    form = TeamMemberAddForm(team, request.POST)
    if form.is_valid():
        member = form.save()
        create_notification(
            recipient=member.user,
            notification_type='team_added',
            title='Вас добавили в команду',
            message=f'Команда «{team.name}» добавила вас в состав.',
            team=team,
            actor=team.leader,
        )
        messages.success(
            request,
            f'{member.user.username} добавлен в команду.',
        )
    else:
        for field, errors in form.errors.items():
            for err in errors:
                if field == '__all__':
                    messages.error(request, err)
                else:
                    label = form.fields[field].label if field in form.fields else field
                    messages.error(request, f'{label}: {err}')

    return redirect(_team_members_tab_url(pk))


@login_required
@require_POST
def team_apply(request, pk):
    """Подать заявку на вступление в команду."""
    team = get_object_or_404(Team, pk=pk)

    if request.user == team.leader:
        messages.error(request, 'Нельзя подать заявку в свою команду.')
        return redirect('accounts:team_profile', pk=pk)
    if request.user.user_type == 'team':
        messages.error(request, 'Аккаунт команды не может подавать заявки.')
        return redirect('accounts:team_profile', pk=pk)
    if not team.is_open_recruitment:
        messages.error(request, 'Набор в команду закрыт.')
        return redirect('accounts:team_profile', pk=pk)
    if TeamMember.objects.filter(team=team, user=request.user).exists():
        messages.info(request, 'Вы уже состоите в этой команде.')
        return redirect('accounts:team_profile', pk=pk)

    form = TeamApplicationForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Не удалось отправить заявку.')
        return redirect('accounts:team_profile', pk=pk)

    try:
        application = TeamApplication.objects.create(
            team=team,
            applicant=request.user,
            message=form.cleaned_data['message'],
        )
    except IntegrityError:
        messages.info(request, 'Заявка уже отправлена и ожидает рассмотрения.')
        return redirect('accounts:team_profile', pk=pk)

    actor_name = request.user.nickname or request.user.username
    create_notification(
        recipient=team.leader,
        notification_type='team_application',
        title='Новая заявка в команду',
        message=f'@{actor_name} подал заявку в команду «{team.name}».',
        team=team,
        application=application,
        actor=request.user,
    )
    messages.success(request, 'Заявка отправлена!')
    return redirect('accounts:team_profile', pk=pk)


@login_required
def team_remove_member(request, pk, membership_pk):
    """Удаление участника из команды (только лидер)."""
    team = get_object_or_404(Team, pk=pk)
    if request.user != team.leader:
        messages.error(request, 'Только лидер может удалять участников.')
        return redirect('accounts:team_profile', pk=pk)
    if request.method != 'POST':
        return redirect(_team_members_tab_url(pk))

    membership = get_object_or_404(TeamMember, pk=membership_pk, team=team)
    username = membership.user.username
    membership.delete()
    messages.success(request, f'{username} удалён из команды.')
    return redirect(_team_members_tab_url(pk))


@login_required

def team_edit(request, pk):

    """Редактирование профиля команды."""

    team = get_object_or_404(Team, pk=pk)



    if request.user != team.leader:

        messages.error(request, 'Только лидер команды может редактировать профиль.')

        return redirect('accounts:team_profile', pk=team.pk)



    if request.method == 'POST':

        form = TeamProfileForm(request.POST, request.FILES, instance=team)

        if form.is_valid():

            form.save()

            messages.success(request, 'Профиль команды обновлён!')

            return redirect('accounts:team_profile', pk=team.pk)

    else:

        form = TeamProfileForm(instance=team)



    context = {

        'form': form,

        'team': team,

    }

    return render(request, 'accounts/team_edit.html', context)





@login_required

def photocard_upload(request, pk):

    """Загрузка фотокарточки в профиль сольного танцора."""

    profile_user = get_object_or_404(CustomUser, pk=pk, user_type='solo')

    if request.user != profile_user:

        raise Http404



    if request.method != 'POST':

        return redirect('accounts:profile', pk=pk)



    form = PhotoCardForm(request.POST, request.FILES, user=profile_user)

    if form.is_valid():

        card = form.save(commit=False)

        card.user = profile_user

        card.save()

        messages.success(request, 'Фотокарточка добавлена!')

    else:

        for field, errors in form.errors.items():

            for error in errors:

                messages.error(request, f'{field}: {error}')



    return redirect(f"{reverse('accounts:profile', kwargs={'pk': pk})}#photocards")





@login_required

def photocard_delete(request, pk, card_pk):

    """Удаление фотокарточки из профиля."""

    profile_user = get_object_or_404(CustomUser, pk=pk, user_type='solo')

    if request.user != profile_user:

        raise Http404



    card = get_object_or_404(PhotoCard, pk=card_pk, user=profile_user)

    card.image.delete(save=False)

    card.delete()

    messages.success(request, 'Фотокарточка удалена.')

    return redirect(f"{reverse('accounts:profile', kwargs={'pk': pk})}#photocards")



from django.shortcuts import render, get_object_or_404, redirect

from django.views.generic import View, DetailView

from django.contrib.auth import login, logout, authenticate

from django.contrib.auth.forms import AuthenticationForm

from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.core.exceptions import ValidationError

from django.db import IntegrityError

from django.db.models import Prefetch, Count

from django.urls import reverse, reverse_lazy

from django.http import Http404, JsonResponse

from django.views.decorators.http import require_POST, require_http_methods



from media_app.moderation import MODERATION_POLICY_MESSAGE

from .models import (
    CustomUser, Team, TeamMember, TeamApplication, Notification, UserProfile,
    OrganizerProfile, SpecialistProfile, PhotoCard, PhotoCardLike,
    PhotoCardComment, PhotoCardCommentLike,
)

from .photocard_utils import record_photo_card_view

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

    PhotoCardCommentForm,

    TeamMemberAddForm,

    TeamApplicationForm,

    DeleteAccountForm,

    normalize_nickname,

    validate_unique_nickname,

    validate_unique_public_username,

    validate_unique_team_username,

)

from media_app.models import CoverMedia

from events.models import Event, EventApplication

from .social_views import get_profile_social_context
from .multi_account import (
    add_linked_account,
    clear_linked_accounts,
    remove_linked_account,
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

    """Находит username для входа по @username или логину."""

    identifier = normalize_nickname(identifier)

    if not identifier:

        return identifier



    user = CustomUser.objects.filter(username__iexact=identifier).first()

    if user:

        return user.username



    user = CustomUser.objects.filter(nickname__iexact=identifier).first()

    if user:

        return user.username



    team = Team.objects.filter(username__iexact=identifier).select_related('leader').first()

    if team:

        return team.leader.username



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

            display_name = user.public_username
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
                        f'Аккаунт @{display_name} добавлен. Вы по-прежнему в @{request.user.public_username}.',
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

    @staticmethod
    def _render(request, user_type='', field_errors=None, form_data=None, add_account=False):
        return render(request, 'accounts/register.html', {
            'field_errors': field_errors or {},
            'form_data': form_data or {},
            'selected_user_type': user_type,
            'add_account': add_account,
        })

    def get(self, request):

        add_account = request.GET.get('add') == '1'
        if request.user.is_authenticated and not add_account:
            return redirect('core:feed')

        return self._render(request, add_account=add_account)



    def post(self, request):

        username = normalize_nickname(request.POST.get('username', ''))

        team_username = normalize_nickname(request.POST.get('team_username', ''))

        team_name = request.POST.get('team_name', '').strip()

        email = request.POST.get('email', '').strip()

        password1 = request.POST.get('password1')

        password2 = request.POST.get('password2')

        user_type = request.POST.get('user_type')

        add_account = request.POST.get('add_account') == '1'

        form_data = {
            'username': username,
            'team_name': team_name,
            'team_username': team_username,
            'email': email,
        }
        field_errors = {}

        if not user_type:
            field_errors['user_type'] = 'Выберите тип аккаунта.'
            return self._render(request, field_errors=field_errors, form_data=form_data, add_account=add_account)

        if password1 != password2:
            field_errors['password2'] = 'Пароли не совпадают.'
            return self._render(request, user_type=user_type, field_errors=field_errors, form_data=form_data, add_account=add_account)

        if not email:
            field_errors['email'] = 'Email обязателен.'
            return self._render(request, user_type=user_type, field_errors=field_errors, form_data=form_data, add_account=add_account)

        if user_type == 'team':
            if not team_username:
                field_errors['team_username'] = 'Укажите username команды.'
                return self._render(request, user_type=user_type, field_errors=field_errors, form_data=form_data, add_account=add_account)
            try:
                validate_unique_public_username(team_username)
            except ValidationError as exc:
                field_errors['team_username'] = exc.messages[0]
                return self._render(request, user_type=user_type, field_errors=field_errors, form_data=form_data, add_account=add_account)
            if not team_name:
                field_errors['team_name'] = 'Укажите название команды.'
                return self._render(request, user_type=user_type, field_errors=field_errors, form_data=form_data, add_account=add_account)
            username = team_username
        else:
            if not username:
                field_errors['username'] = 'Username обязателен.'
                return self._render(request, user_type=user_type, field_errors=field_errors, form_data=form_data, add_account=add_account)
            try:
                validate_unique_public_username(username)
            except ValidationError as exc:
                field_errors['username'] = exc.messages[0]
                return self._render(request, user_type=user_type, field_errors=field_errors, form_data=form_data, add_account=add_account)

        user = CustomUser.objects.create_user(

            username=username,

            email=email,

            password=password1,

            user_type=user_type,

            nickname=None,

        )



        if user_type == 'solo':

            UserProfile.objects.create(user=user)

        elif user_type == 'organizer':

            OrganizerProfile.objects.create(user=user)
            from .organizer_utils import notify_admin_new_organizer
            notify_admin_new_organizer(user)

        elif user_type == 'specialist':

            SpecialistProfile.objects.create(user=user, specialization='other')

        elif user_type == 'team':

            Team.objects.create(

                leader=user,

                name=team_name,

                username=team_username,

            )

        from .admin_notifications import notify_admin_new_user
        notify_admin_new_user(user)

        display_name = user.public_username
        if add_account and request.user.is_authenticated:
            add_linked_account(request, user)
            current_name = request.user.public_username
            messages.success(
                request,
                f'Аккаунт @{display_name} создан и добавлен в переключатель. '
                f'Вы по-прежнему в @{current_name}.',
            )
            return redirect('core:feed')

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

            'is_owner': (
                request.user.is_authenticated
                and request.user.pk == profile_user.pk
            ),

            'cover_style': get_user_cover_style(profile_user),

        }

        context.update(get_profile_social_context(request, profile_user))

        from core.forms import InfoPostForm
        from core.models import InfoPost
        from core.utils import get_kver_admin_user

        admin_user = get_kver_admin_user()
        if admin_user and profile_user.pk == admin_user.pk:
            context.update({
                'is_admin_profile': True,
                'info_posts': InfoPost.objects.select_related('author').order_by('-created_at'),
                'info_post_form': InfoPostForm() if context['is_owner'] else None,
            })
            return render(request, 'accounts/admin_profile.html', context)

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



    is_owner = request.user.is_authenticated and request.user.pk == team.leader_id

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

    pending_applications = []
    if is_owner:
        pending_applications = TeamApplication.objects.filter(
            team=team,
            status='pending',
        ).select_related('applicant').order_by('-created_at')

    context = {

        'team': team,

        'members': members,

        'is_owner': is_owner,

        'profile_user': profile_user,

        'is_team_member': is_team_member,

        'has_pending_application': has_pending_application,

        'pending_applications': pending_applications,

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
@require_POST
def team_application_action(request, pk, application_pk):
    """Принять или отклонить заявку в команду."""
    team = get_object_or_404(Team, pk=pk)
    if request.user != team.leader:
        messages.error(request, 'Только лидер может обрабатывать заявки.')
        return redirect('accounts:team_profile', pk=pk)

    application = get_object_or_404(
        TeamApplication,
        pk=application_pk,
        team=team,
        status='pending',
    )
    action = request.POST.get('action')

    if action == 'accept':
        if team.members_count() >= team.max_members:
            messages.error(request, 'Достигнут лимит участников.')
        elif TeamMember.objects.filter(team=team, user=application.applicant).exists():
            application.status = 'accepted'
            application.save(update_fields=['status'])
            messages.info(request, 'Пользователь уже в команде.')
        else:
            TeamMember.objects.create(
                team=team,
                user=application.applicant,
                role='member',
            )
            application.status = 'accepted'
            application.save(update_fields=['status'])
            create_notification(
                recipient=application.applicant,
                notification_type='team_added',
                title='Заявка принята',
                message=f'Команда «{team.name}» приняла вашу заявку.',
                team=team,
                actor=team.leader,
            )
            messages.success(request, f'{application.applicant.username} принят в команду.')
    elif action == 'reject':
        application.status = 'rejected'
        application.save(update_fields=['status'])
        create_notification(
            recipient=application.applicant,
            notification_type='team_added',
            title='Заявка отклонена',
            message=f'Команда «{team.name}» отклонила вашу заявку.',
            team=team,
            actor=team.leader,
        )
        messages.info(request, 'Заявка отклонена.')
    else:
        messages.error(request, 'Некорректное действие.')

    return redirect(reverse('accounts:team_profile', kwargs={'pk': pk}) + '#applications')


@login_required
@require_POST
def organizer_verification_action(request, pk):
    """Подтверждение или отклонение аккаунта организатора (только администрация)."""
    if not request.user.is_superuser:
        messages.error(request, 'Только администрация может подтверждать организаторов.')
        return redirect('core:feed')

    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user,
        notification_type='organizer_verification',
    )
    organizer = notification.actor
    if not organizer or organizer.user_type != 'organizer':
        messages.error(request, 'Некорректное уведомление.')
        return redirect('core:feed')

    profile, _ = OrganizerProfile.objects.get_or_create(user=organizer)
    action = request.POST.get('action')
    display_name = organizer.nickname or organizer.username

    if action == 'approve':
        profile.is_verified = True
        profile.save(update_fields=['is_verified'])
        create_notification(
            recipient=organizer,
            notification_type='organizer_verified',
            title='Профиль организатора подтверждён',
            message=(
                'Администрация KVER подтвердила ваш аккаунт. '
                'Теперь вы можете создавать мероприятия в календаре.'
            ),
            actor=request.user,
        )
        messages.success(request, f'Организатор @{display_name} подтверждён.')
    elif action == 'reject':
        profile.is_verified = False
        profile.save(update_fields=['is_verified'])
        create_notification(
            recipient=organizer,
            notification_type='organizer_rejected',
            title='Заявка организатора отклонена',
            message=(
                'Администрация KVER отклонила подтверждение аккаунта организатора. '
                'Напишите в поддержку, если считаете это ошибкой.'
            ),
            actor=request.user,
        )
        messages.info(request, f'Заявка организатора @{display_name} отклонена.')
    else:
        messages.error(request, 'Некорректное действие.')
        return redirect('core:feed')

    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return redirect('core:feed')


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


def _account_deletion_warnings(user):
    warnings = [
        'Профиль и персональные данные',
        'Ваши публикации: фото, каверы, мероприятия',
        'Подписки, уведомления и переписка',
    ]
    if user.user_type == 'team':
        warnings.append('Профиль команды, состав и заявки участников')
    elif user.user_type == 'organizer':
        warnings.append('Созданные мероприятия и заявки участников')
    warnings.append(
        'Комментарии на чужих публикациях останутся без ссылки на профиль',
    )
    return warnings


@login_required
@require_http_methods(['GET', 'POST'])
def delete_account(request, pk):
    """Безвозвратное удаление аккаунта пользователем."""
    profile_user = get_object_or_404(CustomUser, pk=pk)
    if request.user.pk != profile_user.pk:
        raise Http404

    if profile_user.is_superuser:
        messages.error(request, 'Аккаунт администратора нельзя удалить через сайт.')
        return redirect('accounts:profile', pk=profile_user.pk)

    if profile_user.user_type == 'team':
        cancel_url = (
            reverse('accounts:team_profile', kwargs={'pk': profile_user.team_profile.pk})
            + '#settings'
        )
    else:
        cancel_url = reverse('accounts:profile', kwargs={'pk': profile_user.pk}) + '#settings'

    if request.method == 'GET':
        return render(request, 'accounts/delete_account.html', {
            'profile_user': profile_user,
            'form': DeleteAccountForm(),
            'deletion_warnings': _account_deletion_warnings(profile_user),
            'cancel_url': cancel_url,
        })

    form = DeleteAccountForm(request.POST)
    if not form.is_valid():
        return render(request, 'accounts/delete_account.html', {
            'profile_user': profile_user,
            'form': form,
            'deletion_warnings': _account_deletion_warnings(profile_user),
            'cancel_url': cancel_url,
        })

    if not authenticate(
        request,
        username=profile_user.username,
        password=form.cleaned_data['password'],
    ):
        form.add_error('password', 'Неверный пароль.')
        return render(request, 'accounts/delete_account.html', {
            'profile_user': profile_user,
            'form': form,
            'deletion_warnings': _account_deletion_warnings(profile_user),
            'cancel_url': cancel_url,
        })

    display = profile_user.public_username
    remaining = remove_linked_account(request, profile_user.pk)
    profile_user.delete()
    logout(request)

    if remaining:
        next_user = CustomUser.objects.filter(pk=remaining[-1]).first()
        if next_user:
            login(request, next_user, backend='django.contrib.auth.backends.ModelBackend')
            request.session[SESSION_KEY] = remaining
            request.session.modified = True
            messages.success(
                request,
                f'Аккаунт @{display} удалён. Вы вошли как @{next_user.public_username}.',
            )
            return redirect('core:feed')

    clear_linked_accounts(request)
    messages.success(request, f'Аккаунт @{display} удалён.')
    return redirect('core:landing')




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

                tags = 'moderation' if str(error) == MODERATION_POLICY_MESSAGE else ''
                messages.error(request, f'{field}: {error}', extra_tags=tags)



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


def _redirect_back(request, fallback):
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect(fallback)


class PhotoCardDetailView(DetailView):
    """Страница фотокарточки с комментариями."""

    model = PhotoCard
    template_name = 'accounts/photocard_detail.html'
    context_object_name = 'card'

    def get_queryset(self):
        return PhotoCard.objects.select_related('user', 'user__profile').prefetch_related(
            'comments__user',
            'comments__user__profile',
        )

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        record_photo_card_view(request, self.object)
        return self.render_to_response(self.get_context_data(object=self.object))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = PhotoCardCommentForm()
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
            context['user_liked'] = PhotoCardLike.objects.filter(
                user=user, photo=self.object,
            ).exists()
            context['user_liked_comment_ids'] = set(
                PhotoCardCommentLike.objects.filter(
                    user=user,
                    comment__in=comments,
                ).values_list('comment_id', flat=True)
            )
        context['likes_count'] = self.object.likes.count()
        context['can_manage_photo'] = user.is_authenticated and (
            user.is_superuser or user.pk == self.object.user_id
        )
        return context


@login_required
@require_POST
def photocard_toggle_like(request, pk):
    """Поставить или убрать лайк с фотокарточки."""
    photo = get_object_or_404(PhotoCard, pk=pk)
    like, created = PhotoCardLike.objects.get_or_create(user=request.user, photo=photo)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        from .social_notifications import notify_photo_like
        notify_photo_like(photo, request.user)
    count = photo.likes.count()
    photo.likes_kver = count
    photo.save(update_fields=['likes_kver'])
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'likes_count': count})
    return _redirect_back(request, reverse('accounts:photocard_detail', kwargs={'pk': pk}))


@login_required
@require_POST
def photocard_comment(request, pk):
    """Добавление комментария к фотокарточке."""
    photo = get_object_or_404(PhotoCard, pk=pk)
    form = PhotoCardCommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.user = request.user
        comment.photo = photo
        comment.is_approved = True
        if not comment.is_anonymous:
            from .comment_utils import comment_author_display_name
            comment.author_display_name = comment_author_display_name(request.user)
        comment.save()
        from .social_notifications import notify_photo_comment
        notify_photo_comment(photo, request.user)
        messages.success(request, 'Комментарий опубликован.')
    else:
        for field_errors in form.errors.values():
            for error in field_errors:
                tags = 'moderation error' if str(error) == MODERATION_POLICY_MESSAGE else 'error'
                messages.error(request, error, extra_tags=tags)
    return redirect(f"{reverse('accounts:photocard_detail', kwargs={'pk': pk})}#comments")


def user_can_delete_photo_comment(user, comment, photo):
    """Удалять комментарий может его автор или владелец фото."""
    if not user.is_authenticated:
        return False
    if comment.user_id == user.pk:
        return True
    return photo.user_id == user.pk


@login_required
@require_POST
def photocard_delete_comment(request, pk, comment_pk):
    """Удаление комментария к фотокарточке."""
    photo = get_object_or_404(PhotoCard, pk=pk)
    comment = get_object_or_404(
        PhotoCardComment,
        pk=comment_pk,
        photo=photo,
        is_approved=True,
    )
    if not user_can_delete_photo_comment(request.user, comment, photo):
        messages.error(request, 'Нет прав для удаления этого комментария.')
        return redirect('accounts:photocard_detail', pk=pk)
    comment.delete()
    messages.success(request, 'Комментарий удалён.')
    return redirect(f"{reverse('accounts:photocard_detail', kwargs={'pk': pk})}#comments")


@login_required
@require_POST
def photocard_toggle_comment_like(request, pk, comment_pk):
    """Поставить или убрать лайк с комментария к фото."""
    comment = get_object_or_404(
        PhotoCardComment,
        pk=comment_pk,
        photo_id=pk,
        is_approved=True,
    )
    like, created = PhotoCardCommentLike.objects.get_or_create(user=request.user, comment=comment)
    if not created:
        like.delete()
    return redirect(f"{reverse('accounts:photocard_detail', kwargs={'pk': pk})}#comments")

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from datetime import date
from dateutil.relativedelta import relativedelta


class CustomUser(AbstractUser):
    """
    Расширенная модель пользователя с различными типами аккаунтов.
    """
    USER_TYPE_CHOICES = [
        ('solo', 'Сольный танцор'),
        ('team', 'Танцевальная команда'),
        ('organizer', 'Организатор мероприятий'),
        ('specialist', 'Специалист (фото/видео/звук)'),
    ]

    user_type = models.CharField(
        max_length=15,
        choices=USER_TYPE_CHOICES,
        default='solo',
        verbose_name='Тип аккаунта'
    )
    nickname = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        verbose_name='Уникальное имя (@username)'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Город'
    )
    bio = models.TextField(
        blank=True,
        verbose_name='О себе (кратко)'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    photo = models.ImageField(
        upload_to='users/photos/',
        blank=True,
        null=True,
        verbose_name='Фото профиля'
    )
    cover_photo = models.ImageField(
        upload_to='users/covers/',
        blank=True,
        null=True,
        verbose_name='Обложка профиля'
    )
    cover_gradient_start = models.CharField(
        max_length=7,
        default='#EC4899',
        verbose_name='Цвет градиента обложки (начало)',
    )
    cover_gradient_end = models.CharField(
        max_length=7,
        default='#8B5CF6',
        verbose_name='Цвет градиента обложки (конец)',
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        verbose_name='Дата рождения'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата регистрации'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    def get_absolute_url(self):
        return reverse('accounts:profile', kwargs={'pk': self.pk})

    @property
    def navbar_photo_url(self):
        """URL фото для аватара в navbar с учётом типа аккаунта."""
        if self.user_type == 'solo':
            try:
                if self.profile.photo:
                    return self.profile.photo.url
            except UserProfile.DoesNotExist:
                pass
        elif self.user_type == 'team':
            try:
                if self.team_profile.logo:
                    return self.team_profile.logo.url
            except Team.DoesNotExist:
                pass
        if self.photo:
            return self.photo.url
        return None

    @property
    def navbar_avatar_shape(self):
        """CSS-класс формы аватара для navbar."""
        shapes = {
            'solo': 'rhombus',
            'team': 'hexagon',
            'organizer': 'square',
            'specialist': 'triangle',
        }
        return shapes.get(self.user_type, 'rhombus')

    @property
    def comment_avatar_shape(self):
        """Форма аватара в комментариях (как в профиле; администрация — круг)."""
        from core.utils import is_kver_admin

        if is_kver_admin(self):
            return 'circle'
        return self.navbar_avatar_shape

    def get_cover_gradient_style(self):
        """CSS-градиент для обложки профиля."""
        start = self.cover_gradient_start or '#EC4899'
        end = self.cover_gradient_end or '#8B5CF6'
        return f'linear-gradient(135deg, {start} 0%, {end} 100%)'

    @property
    def subscribers_count(self):
        """Количество подписчиков профиля."""
        return self.subscribers.count()

    def is_subscribed_by(self, user):
        """Проверяет, подписан ли пользователь на этот профиль."""
        if not user or not user.is_authenticated:
            return False
        if user.pk == self.pk:
            return False
        return self.subscribers.filter(subscriber=user).exists()

    @property
    def public_username(self):
        """Уникальный @username для входа и отображения."""
        if self.user_type == 'team':
            team = getattr(self, 'team_profile', None)
            if team and team.username:
                return team.username
        return self.username

    @property
    def display_name(self):
        """Заголовок профиля: название команды/организации или @username."""
        if self.user_type == 'team':
            team = getattr(self, 'team_profile', None)
            if team and team.name:
                return team.name
        if self.user_type == 'organizer':
            profile = getattr(self, 'organizer_profile', None)
            if profile and profile.organization_name:
                return profile.organization_name
        return self.public_username


class Team(models.Model):
    """
    Модель танцевальной команды.
    """
    leader = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='team_profile',
        verbose_name='Лидер команды',
        limit_choices_to={'user_type': 'team'}
    )
    name = models.CharField(
        max_length=150,
        verbose_name='Название команды'
    )
    username = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Имя пользователя (@username)'
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Город'
    )
    dance_styles = models.CharField(  # ← переименовано с 'style'
        max_length=300,
        blank=True,
        verbose_name='Стили танцев'
    )
    description = models.TextField(
        blank=True,
        verbose_name='Описание команды'
    )
    logo = models.ImageField(  # ← переименовано с 'photo'
        upload_to='teams/logos/',
        blank=True,
        null=True,
        verbose_name='Логотип команды'
    )
    cover_photo = models.ImageField(
        upload_to='teams/covers/',
        blank=True,
        null=True,
        verbose_name='Обложка команды'
    )
    cover_gradient_start = models.CharField(
        max_length=7,
        default='#EC4899',
        verbose_name='Цвет градиента обложки (начало)',
    )
    cover_gradient_end = models.CharField(
        max_length=7,
        default='#8B5CF6',
        verbose_name='Цвет градиента обложки (конец)',
    )
    founded_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Год основания'
    )
    members = models.ManyToManyField(
        CustomUser,
        through='TeamMember',  # ← ПРОМЕЖУТОЧНАЯ ТАБЛИЦА
        related_name='teams_joined',
        blank=True,
        verbose_name='Участники команды'
    )
    is_open_recruitment = models.BooleanField(
        default=True,
        verbose_name='Открыт набор'
    )
    max_members = models.PositiveIntegerField(
        default=20,
        verbose_name='Максимальное количество участников'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Танцевальная команда'
        verbose_name_plural = 'Танцевальные команды'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('accounts:team_profile', kwargs={'pk': self.pk})

    def members_count(self):
        """Количество добавленных участников (без профиля команды)."""
        return self.team_memberships.count()

    @property
    def years_active(self):
        """Автоматический расчёт лет активности команды."""
        if self.founded_year:
            return date.today().year - self.founded_year
        return 0

    def get_cover_gradient_style(self):
        """CSS-градиент для обложки команды."""
        start = self.cover_gradient_start or '#EC4899'
        end = self.cover_gradient_end or '#8B5CF6'
        return f'linear-gradient(135deg, {start} 0%, {end} 100%)'


class TeamMember(models.Model):
    """
    Промежуточная модель для связи Many-to-Many между пользователем и командой.
    Содержит дополнительные атрибуты: роль в команде, дата вступления.
    """
    ROLE_CHOICES = [
        ('leader', 'Лидер'),
        ('member', 'Участник'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='team_memberships',
        verbose_name='Пользователь'
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='team_memberships',
        verbose_name='Команда'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        verbose_name='Роль в команде'
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата вступления'
    )

    class Meta:
        verbose_name = 'Участник команды'
        verbose_name_plural = 'Участники команд'
        unique_together = ['user', 'team']  # один пользователь — одна запись в команде
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.username} в {self.team.name}"


class TeamApplication(models.Model):
    """Заявка соло-танцора на вступление в команду."""

    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('accepted', 'Принята'),
        ('rejected', 'Отклонена'),
    ]

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='Команда',
    )
    applicant = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='team_applications',
        verbose_name='Заявитель',
    )
    message = models.TextField(
        blank=True,
        verbose_name='Сообщение',
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата заявки',
    )

    class Meta:
        verbose_name = 'Заявка в команду'
        verbose_name_plural = 'Заявки в команды'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['team', 'applicant'],
                condition=models.Q(status='pending'),
                name='unique_pending_team_application',
            ),
        ]

    def __str__(self):
        return f'{self.applicant.username} → {self.team.name}'


class Notification(models.Model):
    """In-app уведомление для пользователя."""

    TYPE_CHOICES = [
        ('team_application', 'Заявка в команду'),
        ('team_added', 'Добавлен в команду'),
        ('event_application', 'Заявка на мероприятие'),
        ('organizer_verification', 'Подтверждение организатора'),
        ('organizer_verified', 'Организатор подтверждён'),
        ('organizer_rejected', 'Организатор отклонён'),
        ('new_user_registration', 'Новая регистрация'),
        ('new_subscriber', 'Новый подписчик'),
        ('photo_like', 'Лайк на фото'),
        ('photo_comment', 'Комментарий к фото'),
        ('cover_like', 'Лайк на публикацию'),
        ('cover_comment', 'Комментарий к публикации'),
        ('new_message', 'Новое сообщение'),
    ]

    recipient = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='Получатель',
    )
    notification_type = models.CharField(
        max_length=30,
        choices=TYPE_CHOICES,
        verbose_name='Тип',
    )
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    message = models.TextField(verbose_name='Текст')
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Команда',
    )
    application = models.ForeignKey(
        TeamApplication,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Заявка',
    )
    event = models.ForeignKey(
        'events.Event',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Мероприятие',
    )
    actor = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_sent',
        verbose_name='Инициатор',
    )
    photo = models.ForeignKey(
        'PhotoCard',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Фотокарточка',
    )
    cover = models.ForeignKey(
        'media_app.CoverMedia',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Публикация',
    )
    conversation = models.ForeignKey(
        'Conversation',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='Диалог',
    )
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} → {self.recipient.username}'

    def get_target_url(self):
        from django.urls import reverse
        if self.notification_type == 'new_user_registration' and self.actor_id:
            actor = self.actor
            if actor.user_type == 'team':
                team = getattr(actor, 'team_profile', None)
                if team:
                    return reverse('accounts:team_profile', kwargs={'pk': team.pk})
            return reverse('accounts:profile', kwargs={'pk': self.actor_id})
        if self.notification_type == 'organizer_verification' and self.actor_id:
            return reverse('accounts:profile', kwargs={'pk': self.actor_id})
        if self.notification_type in ('organizer_verified', 'organizer_rejected'):
            return reverse('accounts:profile', kwargs={'pk': self.recipient_id})
        if self.notification_type == 'team_application' and self.team_id:
            return reverse('accounts:team_profile', kwargs={'pk': self.team_id}) + '#applications'
        if self.notification_type == 'event_application' and self.event_id:
            return reverse('events:detail', kwargs={'pk': self.event_id})
        if self.notification_type == 'new_subscriber' and self.actor_id:
            return reverse('accounts:profile', kwargs={'pk': self.actor_id})
        if self.notification_type in ('photo_like', 'photo_comment') and self.photo_id:
            return reverse('accounts:photocard_detail', kwargs={'pk': self.photo_id})
        if self.notification_type in ('cover_like', 'cover_comment') and self.cover_id:
            return reverse('media_app:detail', kwargs={'pk': self.cover_id})
        if self.notification_type == 'new_message' and self.conversation_id:
            conv = self.conversation
            if conv.participant1_id == self.recipient_id:
                return reverse('accounts:chat', kwargs={'pk': conv.participant2_id})
            return reverse('accounts:chat', kwargs={'pk': conv.participant1_id})
        if self.team_id:
            return reverse('accounts:team_profile', kwargs={'pk': self.team_id})
        return reverse('accounts:profile', kwargs={'pk': self.recipient_id})


class UserProfile(models.Model):
    """
    Расширенный профиль для сольных танцоров.
    Содержит все поля, описанные в дипломе (Таблица 12).
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='Пользователь'
    )
    # === Танцевальная информация ===
    dance_level = models.CharField(
        max_length=50,
        blank=True,
        choices=[
            ('beginner', 'Начинающий'),
            ('intermediate', 'Средний'),
            ('advanced', 'Продвинутый'),
            ('professional', 'Профессионал'),
        ],
        verbose_name='Уровень подготовки'
    )
    dance_positions = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Позиция в танце'
    )
    dance_styles = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Стили танцев'
    )
    favorite_groups = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Любимые группы'
    )
    # === ВАЖНО: дата начала занятий (для автоподсчёта стажа) ===
    experience_start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='Дата начала занятий танцами'
    )
    # === Расширенная информация ===
    bio = models.TextField(  # ← ДОБАВЛЕНО
        blank=True,
        verbose_name='О себе (подробно)'
    )
    mbti = models.CharField(
        max_length=4,
        blank=True,
        verbose_name='Тип MBTI'
    )
    height = models.PositiveIntegerField(
        blank=True,
        null=True,
        verbose_name='Рост (см)'
    )
    is_available_for_collab = models.BooleanField(
        default=True,
        verbose_name='Доступен для коллабораций'
    )
    # === Социальные сети (JSON) ===
    social_links = models.JSONField(  # ← ДОБАВЛЕНО
        blank=True,
        null=True,
        verbose_name='Ссылки на соцсети',
        help_text='Формат: {"vk": "ссылка", "telegram": "@username", "instagram": "@username"}'
    )
    # === Медиа профиля ===
    photo = models.ImageField(  # ← ДОБАВЛЕНО
        upload_to='profiles/photos/',
        blank=True,
        null=True,
        verbose_name='Фото профиля'
    )
    cover_photo = models.ImageField(  # ← ДОБАВЛЕНО
        upload_to='profiles/covers/',
        blank=True,
        null=True,
        verbose_name='Обложка профиля'
    )
    cover_gradient_start = models.CharField(
        max_length=7,
        default='#EC4899',
        verbose_name='Цвет градиента обложки (начало)',
    )
    cover_gradient_end = models.CharField(
        max_length=7,
        default='#8B5CF6',
        verbose_name='Цвет градиента обложки (конец)',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Профиль танцора'
        verbose_name_plural = 'Профили танцоров'

    def __str__(self):
        return f"Профиль {self.user.username}"

    @property
    def dance_experience(self):
        """
        Автоматический расчёт танцевального стажа.
        Возвращает строку вида "3 года 6 месяцев" или "8 месяцев".
        """
        if not self.experience_start_date:
            return "Не указано"

        delta = relativedelta(date.today(), self.experience_start_date)
        if delta.years > 0:
            return f"{delta.years} г. {delta.months} мес."
        elif delta.months > 0:
            return f"{delta.months} мес."
        else:
            return f"{delta.days} дн."

    def get_cover_gradient_style(self):
        """CSS-градиент для обложки сольного профиля."""
        start = self.cover_gradient_start or '#EC4899'
        end = self.cover_gradient_end or '#8B5CF6'
        return f'linear-gradient(135deg, {start} 0%, {end} 100%)'


class PhotoAlbum(models.Model):
    """Альбом фотокарточек пользователя."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='photo_albums',
        verbose_name='Пользователь',
    )
    title = models.CharField(max_length=150, verbose_name='Название альбома')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Фотоальбом'
        verbose_name_plural = 'Фотоальбомы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} — {self.user.username}'


class PhotoCard(models.Model):
    """Фотокарточка в профиле сольного танцора."""

    LINK_TYPE_CHOICES = [
        ('none', 'Без ссылки'),
        ('event', 'Мероприятие'),
        ('cover', 'Кавер'),
        ('performance', 'Выступление'),
        ('url', 'Другая ссылка'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='photo_cards',
        verbose_name='Пользователь',
    )
    image = models.ImageField(
        upload_to='photo_cards/',
        verbose_name='Фото',
    )
    album = models.ForeignKey(
        PhotoAlbum,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photos',
        verbose_name='Альбом',
    )
    tagged_users = models.ManyToManyField(
        CustomUser,
        blank=True,
        related_name='tagged_in_photo_cards',
        verbose_name='Отмеченные пользователи',
    )
    caption = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Подпись',
    )
    link_type = models.CharField(
        max_length=20,
        choices=LINK_TYPE_CHOICES,
        default='none',
        verbose_name='Тип ссылки',
    )
    link_url = models.URLField(
        blank=True,
        verbose_name='Ссылка',
    )
    linked_event = models.ForeignKey(
        'events.Event',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photo_cards',
        verbose_name='Мероприятие',
    )
    linked_cover = models.ForeignKey(
        'media_app.CoverMedia',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='photo_cards',
        verbose_name='Кавер',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )
    views_kver = models.PositiveIntegerField(
        default=0,
        verbose_name='Просмотры на KVER',
    )
    likes_kver = models.PositiveIntegerField(
        default=0,
        verbose_name='Лайки на KVER',
    )

    class Meta:
        verbose_name = 'Фотокарточка'
        verbose_name_plural = 'Фотокарточки'
        ordering = ['-created_at']

    def __str__(self):
        return f'Фотокарточка {self.user.username} — {self.created_at:%d.%m.%Y}'

    def get_link_display_url(self):
        """Возвращает URL для отображения ссылки на карточке."""
        if self.link_type == 'event' and self.linked_event_id:
            return self.linked_event.get_absolute_url()
        if self.link_type == 'cover' and self.linked_cover_id:
            return reverse('media_app:detail', kwargs={'pk': self.linked_cover_id})
        if self.link_url:
            return self.link_url
        return None

    def get_link_label(self):
        """Текст ссылки для отображения на карточке."""
        labels = {
            'event': 'Мероприятие',
            'cover': 'Кавер',
            'performance': 'Выступление',
            'url': 'Ссылка',
        }
        if self.link_type == 'event' and self.linked_event_id:
            return self.linked_event.title
        if self.link_type == 'cover' and self.linked_cover_id:
            return self.linked_cover.title
        return labels.get(self.link_type, '')

    def get_absolute_url(self):
        return reverse('accounts:photocard_detail', kwargs={'pk': self.pk})


class PhotoCardDailyView(models.Model):
    """Один просмотр фотокарточки от пользователя или сессии за календарные сутки."""

    photo = models.ForeignKey(
        PhotoCard,
        on_delete=models.CASCADE,
        related_name='daily_views',
        verbose_name='Фотокарточка',
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='photocard_daily_views',
        verbose_name='Пользователь',
    )
    session_key = models.CharField(max_length=40, blank=True, default='')
    viewer_key = models.CharField(max_length=128, verbose_name='Ключ зрителя')
    view_date = models.DateField(verbose_name='Дата просмотра')

    class Meta:
        verbose_name = 'Дневной просмотр фото'
        verbose_name_plural = 'Дневные просмотры фото'
        constraints = [
            models.UniqueConstraint(
                fields=['photo', 'viewer_key', 'view_date'],
                name='unique_photocard_daily_view',
            ),
        ]


class PhotoCardLike(models.Model):
    """Лайк пользователя на фотокарточку."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='photocard_likes',
        verbose_name='Пользователь',
    )
    photo = models.ForeignKey(
        PhotoCard,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Фотокарточка',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Лайк фото'
        verbose_name_plural = 'Лайки фото'
        constraints = [
            models.UniqueConstraint(fields=['user', 'photo'], name='unique_photocard_like'),
        ]


class PhotoCardComment(models.Model):
    """Комментарий к фотокарточке."""

    photo = models.ForeignKey(
        PhotoCard,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Фотокарточка',
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Автор',
    )
    text = models.TextField(verbose_name='Текст комментария')
    is_anonymous = models.BooleanField(default=False, verbose_name='Анонимно')
    author_display_name = models.CharField(
        max_length=150,
        blank=True,
        verbose_name='Имя автора (снимок)',
        help_text='Сохраняется при удалении аккаунта автора.',
    )
    is_approved = models.BooleanField(default=False, verbose_name='Прошёл модерацию')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')

    class Meta:
        verbose_name = 'Комментарий к фото'
        verbose_name_plural = 'Комментарии к фото'
        ordering = ['created_at']

    def __str__(self):
        author_name = 'Аноним' if self.is_anonymous else (self.user.username if self.user else 'Удалён')
        return f'Комментарий к фото #{self.photo_id} от {author_name}'


class PhotoCardCommentLike(models.Model):
    """Лайк пользователя на комментарий к фото."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='photocard_comment_likes',
        verbose_name='Пользователь',
    )
    comment = models.ForeignKey(
        PhotoCardComment,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name='Комментарий',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Лайк комментария к фото'
        verbose_name_plural = 'Лайки комментариев к фото'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'comment'],
                name='unique_photocard_comment_like',
            ),
        ]


class Subscription(models.Model):
    """Подписка одного пользователя на профиль другого."""

    subscriber = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    target = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Профиль',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата подписки')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'target'],
                name='unique_subscription',
            ),
        ]

    def __str__(self):
        return f'{self.subscriber.username} → {self.target.username}'


class Conversation(models.Model):
    """Диалог между двумя пользователями."""

    participant1 = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='conversations_as_p1',
        verbose_name='Участник 1',
    )
    participant2 = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='conversations_as_p2',
        verbose_name='Участник 2',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создан')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлён')

    class Meta:
        verbose_name = 'Диалог'
        verbose_name_plural = 'Диалоги'
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['participant1', 'participant2'],
                name='unique_conversation_pair',
            ),
        ]

    def __str__(self):
        return f'Диалог {self.participant1.username} — {self.participant2.username}'

    @classmethod
    def get_or_create_for_users(cls, user_a, user_b):
        """Возвращает диалог между двумя пользователями (порядок фиксирован по pk)."""
        if user_a.pk > user_b.pk:
            user_a, user_b = user_b, user_a
        conversation, _ = cls.objects.get_or_create(
            participant1=user_a,
            participant2=user_b,
        )
        return conversation

    def other_participant(self, user):
        """Второй участник диалога относительно текущего пользователя."""
        if user.pk == self.participant1_id:
            return self.participant2
        return self.participant1

    def last_message(self):
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """Сообщение в диалоге."""

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Диалог',
    )
    sender = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name='Отправитель',
    )
    text = models.TextField(verbose_name='Текст')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата')
    is_read = models.BooleanField(default=False, verbose_name='Прочитано')

    class Meta:
        verbose_name = 'Сообщение'
        verbose_name_plural = 'Сообщения'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username}: {self.text[:40]}'


class OrganizerProfile(models.Model):
    """
    Профиль организатора мероприятий.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='organizer_profile',
        verbose_name='Пользователь'
    )
    organization_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Название организации'
    )
    website = models.URLField(
        blank=True,
        verbose_name='Сайт'
    )
    social_media = models.TextField(
        blank=True,
        help_text='Ссылки на социальные сети (каждая с новой строки)',
        verbose_name='Социальные сети'
    )
    experience_description = models.TextField(
        blank=True,
        verbose_name='Опыт работы'
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name='Проверенный организатор'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Профиль организатора'
        verbose_name_plural = 'Профили организаторов'

    def __str__(self):
        return f"Организатор {self.user.username}"


class SpecialistProfile(models.Model):
    """
    Профиль специалиста (фотограф, оператор, звукорежиссер).
    """
    SPECIALIZATION_CHOICES = [
        ('photographer', 'Фотограф'),
        ('videographer', 'Видеооператор'),
        ('sound_engineer', 'Звукорежиссер'),
        ('editor', 'Монтажер'),
        ('choreographer', 'Хореограф-постановщик'),
        ('other', 'Другое'),
    ]

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='specialist_profile',
        verbose_name='Пользователь'
    )
    specialization = models.CharField(
        max_length=50,
        choices=SPECIALIZATION_CHOICES,
        verbose_name='Специализация'
    )
    portfolio_description = models.TextField(
        blank=True,
        verbose_name='Описание портфолио'
    )
    price_range = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Ценовой диапазон'
    )
    is_available = models.BooleanField(
        default=True,
        verbose_name='Доступен для заказов'
    )
    equipment = models.TextField(
        blank=True,
        verbose_name='Оборудование'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Профиль специалиста'
        verbose_name_plural = 'Профили специалистов'

    def __str__(self):
        return f"{self.get_specialization_display()} - {self.user.username}"
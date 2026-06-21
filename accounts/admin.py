from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Team, TeamMember, TeamApplication, Notification, UserProfile, OrganizerProfile, SpecialistProfile, PhotoCard, Subscription, Conversation, Message, PhotoAlbum


# ==========================================
# КАСТОМНЫЙ ПОЛЬЗОВАТЕЛЬ
# ==========================================

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'city', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'city')
    search_fields = ('username', 'email', 'nickname')
    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Дополнительная информация', {
            'fields': ('user_type', 'nickname', 'city', 'phone', 'photo', 'cover_photo', 'date_of_birth')
        }),
    )


# ==========================================
# ПРОФИЛИ
# ==========================================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'dance_level', 'dance_positions', 'dance_styles', 'experience_start_date', 'created_at')
    list_filter = ('dance_level', 'is_available_for_collab')
    search_fields = ('user__username', 'dance_styles', 'favorite_groups')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Основное', {
            'fields': ('user', 'photo', 'cover_photo', 'bio')
        }),
        ('Танцевальная информация', {
            'fields': (
            'dance_level', 'dance_positions', 'dance_styles', 'favorite_groups', 'experience_start_date', 'mbti',
            'height')
        }),
        ('Социальные сети', {
            'fields': ('social_links', 'is_available_for_collab')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrganizerProfile)
class OrganizerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization_name', 'is_verified', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('user__username', 'organization_name')
    readonly_fields = ('created_at',)


@admin.register(SpecialistProfile)
class SpecialistProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'price_range', 'is_available', 'created_at')
    list_filter = ('specialization', 'is_available')
    search_fields = ('user__username', 'portfolio_description')
    readonly_fields = ('created_at',)


# ==========================================
# КОМАНДЫ И УЧАСТНИКИ
# ==========================================

# Inline для управления участниками прямо на странице команды
class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 1  # Сколько пустых строк показывать по умолчанию
    fields = ('user', 'role')
    autocomplete_fields = ('user',)  # Удобный поиск пользователя по нику


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'joined_at')
    list_filter = ('role', 'team')
    search_fields = ('user__username', 'team__name')


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = (
    'name', 'username', 'city', 'dance_styles', 'founded_year', 'is_open_recruitment', 'members_count', 'created_at')
    list_filter = ('city', 'is_open_recruitment', 'founded_year')
    search_fields = ('name', 'username', 'description')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Основное', {
            'fields': ('leader', 'name', 'username', 'logo', 'cover_photo')
        }),
        ('Информация', {
            'fields': ('city', 'dance_styles', 'description', 'founded_year')
        }),
        ('Настройки', {
            # Убрали 'members' отсюда, так как теперь они управляются через Inline ниже
            'fields': ('is_open_recruitment', 'max_members')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # Подключаем инлайн, чтобы добавлять участников прямо на странице команды
    inlines = [TeamMemberInline]

    def members_count(self, obj):
        return obj.members_count()

    members_count.short_description = 'Участников'


@admin.register(PhotoCard)
class PhotoCardAdmin(admin.ModelAdmin):
    list_display = ('user', 'caption', 'link_type', 'created_at')
    list_filter = ('link_type',)
    search_fields = ('user__username', 'caption')
    autocomplete_fields = ('user', 'linked_event', 'linked_cover', 'album')
    filter_horizontal = ('tagged_users',)


@admin.register(PhotoAlbum)
class PhotoAlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at')
    search_fields = ('title', 'user__username')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('subscriber', 'target', 'created_at')
    search_fields = ('subscriber__username', 'target__username')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('participant1', 'participant2', 'updated_at')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'created_at', 'is_read')
    list_filter = ('is_read',)


@admin.register(TeamApplication)
class TeamApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant', 'team', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('applicant__username', 'team__name')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('recipient__username', 'title')
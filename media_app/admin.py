from django.contrib import admin

from .models import CoverMedia, Comment


@admin.register(CoverMedia)
class CoverMediaAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'source_type', 'is_approved', 'created_at')
    list_filter = ('source_type', 'is_approved', 'created_at')
    search_fields = ('title', 'tags', 'author__username', 'description')
    filter_horizontal = ('mentioned_users',)
    ordering = ['-created_at']
    actions = ['approve_selected']

    def approve_selected(self, request, queryset):
        queryset.update(is_approved=True)

    approve_selected.short_description = 'Одобрить выбранные публикации'


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('media', 'user', 'is_anonymous', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'is_anonymous')
    search_fields = ('text', 'user__username', 'media__title')
    ordering = ['-created_at']
    actions = ['approve_selected']

    def approve_selected(self, request, queryset):
        queryset.update(is_approved=True)

    approve_selected.short_description = 'Одобрить выбранные комментарии'

from django.contrib import admin

from .models import InfoPost


@admin.register(InfoPost)
class InfoPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at')
    search_fields = ('title', 'body')
    list_filter = ('created_at',)

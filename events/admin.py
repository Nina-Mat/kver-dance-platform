from django.contrib import admin



from .models import Event, EventApplication





class EventApplicationInline(admin.TabularInline):

    model = EventApplication

    extra = 0

    readonly_fields = ('applicant', 'status', 'created_at')

    fields = ('applicant', 'status', 'audio_file', 'created_at')





@admin.register(Event)

class EventAdmin(admin.ModelAdmin):

    list_display = (

        'title',

        'organizer',

        'event_type',

        'event_date',

        'location',

        'is_published',

    )

    list_filter = ('event_type', 'is_published', 'event_date')

    search_fields = ('title', 'location', 'organizer__username')

    ordering = ['-event_date']

    inlines = [EventApplicationInline]





@admin.register(EventApplication)

class EventApplicationAdmin(admin.ModelAdmin):

    list_display = ('event', 'applicant', 'status', 'created_at')

    list_filter = ('status', 'created_at')

    search_fields = ('event__title', 'applicant__username')

    ordering = ['-created_at']


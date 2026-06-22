from django.urls import path

from . import views

app_name = 'events'

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
    path('create/', views.event_create, name='create'),
    path('<int:pk>/edit/', views.event_edit, name='edit'),
    path('location/suggest/', views.location_suggest, name='location_suggest'),
    path('<int:pk>/apply/', views.event_apply, name='apply'),
    path('<int:pk>/applications/', views.event_applications, name='applications'),
    path('applications/<int:pk>/status/', views.application_update_status, name='application_status'),
    path('<int:pk>/', views.event_detail, name='detail'),
]

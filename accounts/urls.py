from django.urls import path

from . import views
from . import social_views
from . import account_switch_views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('switch/<int:pk>/', account_switch_views.switch_account, name='switch_account'),
    path('remove/<int:pk>/', account_switch_views.remove_account, name='remove_account'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/<int:pk>/', views.ProfileView.as_view(), name='profile'),
    path('profile/<int:pk>/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('team/<int:pk>/members/<int:membership_pk>/remove/', views.team_remove_member, name='team_remove_member'),
    path('team/<int:pk>/members/add/', views.team_add_member, name='team_add_member'),
    path('team/<int:pk>/apply/', views.team_apply, name='team_apply'),
    path('team/<int:pk>/edit/', views.team_edit, name='team_edit'),
    path('team/<int:pk>/', views.team_profile, name='team_profile'),
    path('profile/<int:pk>/photocard/', views.photocard_upload, name='photocard_upload'),
    path('profile/<int:pk>/photocard/<int:card_pk>/delete/', views.photocard_delete, name='photocard_delete'),
    path('subscribe/<int:pk>/', social_views.subscribe, name='subscribe'),
    path('unsubscribe/<int:pk>/', social_views.unsubscribe, name='unsubscribe'),
    path('notifications/<int:pk>/read/', social_views.notification_read, name='notification_read'),
    path('subscriptions/suggest/', social_views.subscription_suggest, name='subscription_suggest'),
    path('subscriptions/', social_views.subscriptions_list, name='subscriptions'),
    path('messenger/', social_views.messenger_list, name='messenger'),
    path('messenger/<int:pk>/', social_views.chat_detail, name='chat'),
    path('photos/', social_views.photos_section, name='photos'),
]

from django.urls import path

from . import views

app_name = 'media_app'

urlpatterns = [
    path('feed/', views.CoverMediaFeedView.as_view(), name='feed'),
    path('covers/', views.CoversFeedView.as_view(), name='covers_feed'),
    path('performances/', views.PerformancesFeedView.as_view(), name='performances_feed'),
    path('upload/', views.CoverMediaCreateView.as_view(), name='upload'),
    path('preview-youtube/', views.youtube_preview, name='youtube_preview'),
    path('<int:pk>/', views.CoverMediaDetailView.as_view(), name='detail'),
    path('<int:pk>/comment/', views.CommentCreateView.as_view(), name='comment'),
]

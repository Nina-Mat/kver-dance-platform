from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.LandingView.as_view(), name='landing'),
    path('feed/', views.FeedView.as_view(), name='feed'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('search/suggest/', views.search_suggest, name='search_suggest'),
    path('teams/', views.TeamsView.as_view(), name='teams'),
    path('specialists/', views.SpecialistsView.as_view(), name='specialists'),
]
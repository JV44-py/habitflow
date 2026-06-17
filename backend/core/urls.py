"""
HabitFlow API URL Configuration
All REST API endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'habits', views.HabitViewSet, basename='habit')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'goals', views.GoalViewSet, basename='goal')

urlpatterns = [
    path('', include(router.urls)),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('analytics/', views.AnalyticsView.as_view(), name='analytics'),
    path('achievements/', views.AchievementView.as_view(), name='achievements'),
    path('calendar/', views.CalendarView.as_view(), name='calendar'),
]

"""
Page URL routes — serves HTML frontend pages.
Habits page uses a real view to pass routine context.
"""

from django.urls import path
from django.views.generic import TemplateView
from . import page_views

urlpatterns = [
    path('',              TemplateView.as_view(template_name='core/index.html'),        name='home'),
    path('login/',        TemplateView.as_view(template_name='core/auth.html'),         name='login'),
    path('register/',     TemplateView.as_view(template_name='core/auth.html'),         name='register'),
    path('dashboard/',    TemplateView.as_view(template_name='core/dashboard.html'),    name='dashboard-page'),
    path('habits/',       page_views.habits_page,                                        name='habits-page'),
    path('analytics/',    TemplateView.as_view(template_name='core/analytics.html'),    name='analytics-page'),
    path('achievements/', TemplateView.as_view(template_name='core/achievements.html'), name='achievements-page'),
    path('profile/',      TemplateView.as_view(template_name='core/profile.html'),      name='profile-page'),
    path('calendar/',     TemplateView.as_view(template_name='core/calendar.html'),     name='calendar-page'),
]

"""
Page views — render HTML templates with context data.
No authentication is enforced here; JS handles auth redirects.
"""

from django.shortcuts import render


def habits_page(request):
    """Habits page with routine context for template loops."""
    routines = [
        ('morning',   'Morning',   '🌅'),
        ('afternoon', 'Afternoon', '☀️'),
        ('evening',   'Evening',   '🌙'),
        ('anytime',   'Anytime',   '⭐'),
    ]
    return render(request, 'core/habits.html', {'routines': routines})

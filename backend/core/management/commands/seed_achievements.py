"""
Seed default achievements into the database.
Run: python manage.py seed_achievements
"""

from django.core.management.base import BaseCommand
from core.models import Achievement


class Command(BaseCommand):
    help = 'Seed default achievements'

    def handle(self, *args, **options):
        achievements = [
            # Streak achievements
            {'title': 'First Step', 'description': 'Complete a habit for the first time', 'badge_icon': '👣', 'badge_type': 'completion', 'xp_reward': 25, 'requirement_value': 1},
            {'title': '3-Day Warrior', 'description': 'Maintain a 3-day streak', 'badge_icon': '🔥', 'badge_type': 'streak', 'xp_reward': 50, 'requirement_value': 3},
            {'title': 'Week Champion', 'description': 'Maintain a 7-day streak', 'badge_icon': '🏆', 'badge_type': 'streak', 'xp_reward': 100, 'requirement_value': 7},
            {'title': 'Fortnight Master', 'description': 'Maintain a 14-day streak', 'badge_icon': '⚡', 'badge_type': 'streak', 'xp_reward': 200, 'requirement_value': 14},
            {'title': 'Month Legend', 'description': 'Maintain a 30-day streak', 'badge_icon': '👑', 'badge_type': 'streak', 'xp_reward': 500, 'requirement_value': 30},
            {'title': '100 Day Hero', 'description': 'Maintain a 100-day streak', 'badge_icon': '💎', 'badge_type': 'streak', 'xp_reward': 1000, 'requirement_value': 100},
            # Completion achievements
            {'title': 'Getting Started', 'description': 'Complete 10 habits total', 'badge_icon': '🌱', 'badge_type': 'completion', 'xp_reward': 50, 'requirement_value': 10},
            {'title': 'Consistent', 'description': 'Complete 50 habits total', 'badge_icon': '💪', 'badge_type': 'completion', 'xp_reward': 150, 'requirement_value': 50},
            {'title': 'Dedicated', 'description': 'Complete 100 habits total', 'badge_icon': '🎯', 'badge_type': 'completion', 'xp_reward': 300, 'requirement_value': 100},
            {'title': 'Unstoppable', 'description': 'Complete 500 habits total', 'badge_icon': '🚀', 'badge_type': 'completion', 'xp_reward': 1000, 'requirement_value': 500},
            # Milestone achievements
            {'title': 'Habit Builder', 'description': 'Create your first 3 habits', 'badge_icon': '🏗️', 'badge_type': 'milestone', 'xp_reward': 75, 'requirement_value': 3},
            {'title': 'Habit Architect', 'description': 'Create 10 habits', 'badge_icon': '🗺️', 'badge_type': 'milestone', 'xp_reward': 200, 'requirement_value': 10},
        ]

        created = 0
        for data in achievements:
            obj, was_created = Achievement.objects.get_or_create(
                title=data['title'],
                defaults=data
            )
            if was_created:
                created += 1

        self.stdout.write(
            self.style.SUCCESS(f'✅ Seeded {created} new achievements ({len(achievements)} total)')
        )

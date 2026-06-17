"""
HabitFlow API Views
Complete REST API for habit tracking, analytics, and gamification
"""

import random
from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Count, Q, Avg
from django.db import transaction
from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, Category, Habit, HabitCompletion, Achievement, UserAchievement, Goal
from .serializers import (
    UserProfileSerializer, CategorySerializer, HabitSerializer,
    HabitCreateSerializer, HabitCompletionSerializer, AchievementSerializer,
    UserAchievementSerializer, GoalSerializer
)

MOTIVATIONAL_QUOTES = [
    {"text": "We are what we repeatedly do. Excellence, then, is not an act, but a habit.", "author": "Aristotle"},
    {"text": "Small daily improvements over time lead to stunning results.", "author": "Robin Sharma"},
    {"text": "Motivation is what gets you started. Habit is what keeps you going.", "author": "Jim Ryun"},
    {"text": "You'll never change your life until you change something you do daily.", "author": "John C. Maxwell"},
    {"text": "Success is the sum of small efforts repeated day in and day out.", "author": "Robert Collier"},
    {"text": "The secret of getting ahead is getting started.", "author": "Mark Twain"},
    {"text": "A journey of a thousand miles begins with a single step.", "author": "Lao Tzu"},
    {"text": "Habits are the compound interest of self-improvement.", "author": "James Clear"},
    {"text": "Every action you take is a vote for the type of person you want to become.", "author": "James Clear"},
    {"text": "Don't count the days. Make the days count.", "author": "Muhammad Ali"},
]


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get and update user profile"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class DashboardView(APIView):
    """Dashboard data aggregation"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        # Today's habits
        active_habits = user.habits.filter(is_active=True)
        
        today_completions = HabitCompletion.objects.filter(
            habit__user=user,
            completion_date=today,
            completed=True
        ).count()
        
        total_today = active_habits.count()
        today_rate = (today_completions / total_today * 100) if total_today > 0 else 0

        # Weekly completion rate
        week_completions = HabitCompletion.objects.filter(
            habit__user=user,
            completion_date__gte=week_ago,
            completed=True
        ).count()
        total_week = active_habits.count() * 7
        weekly_rate = (week_completions / total_week * 100) if total_week > 0 else 0

        # Best current streak across all habits
        best_streak = active_habits.aggregate(
            max_streak=Count('current_streak')
        )
        current_streak = active_habits.order_by('-current_streak').first()
        streak_val = current_streak.current_streak if current_streak else 0

        # Recent achievements
        recent_achievements = user.user_achievements.select_related('achievement').order_by('-unlocked_at')[:3]

        # Habits by routine for today
        habits_data = HabitSerializer(active_habits, many=True, context={'request': request}).data

        return Response({
            'user': UserProfileSerializer(user).data,
            'today_habits': habits_data,
            'today_completion_count': today_completions,
            'today_total': total_today,
            'today_completion_rate': round(today_rate, 1),
            'weekly_completion_rate': round(weekly_rate, 1),
            'total_active_habits': total_today,
            'current_streak': streak_val,
            'recent_achievements': UserAchievementSerializer(recent_achievements, many=True).data,
            'motivational_quote': random.choice(MOTIVATIONAL_QUOTES),
        })


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD for habit categories"""
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class HabitViewSet(viewsets.ModelViewSet):
    """Full CRUD for habits"""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return HabitCreateSerializer
        return HabitSerializer

    def get_queryset(self):
        queryset = Habit.objects.filter(
            user=self.request.user, is_active=True
        ).select_related('category')
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category_id=category)
        
        # Filter by routine
        routine = self.request.query_params.get('routine')
        if routine:
            queryset = queryset.filter(routine=routine)
        
        # Filter by difficulty
        difficulty = self.request.query_params.get('difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        # Search
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )
        
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Soft delete habit"""
        habit = self.get_object()
        habit.is_active = False
        habit.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def toggle_complete(self, request, pk=None):
        """Toggle habit completion for today"""
        habit = self.get_object()
        today = timezone.now().date()
        
        completion, created = HabitCompletion.objects.get_or_create(
            habit=habit,
            completion_date=today,
            defaults={'completed': False}
        )
        
        with transaction.atomic():
            # Toggle completion
            completion.completed = not completion.completed
            if completion.completed:
                completion.completed_at = timezone.now()
                completion.notes = request.data.get('notes', '')
                completion.mood = request.data.get('mood')
            else:
                completion.completed_at = None
            completion.save()
            
            # Update streak and XP
            if completion.completed:
                self._update_streak(habit, today)
                self._award_xp(habit, request.user)
            else:
                self._recalculate_streak(habit)
                self._remove_xp(habit, request.user)
        
        # Check achievements
        self._check_achievements(request.user)
        
        return Response({
            'completed': completion.completed,
            'streak': habit.current_streak,
            'xp_earned': habit.xp_reward if completion.completed else 0,
            'user_xp': request.user.xp_points,
            'user_level': request.user.level,
        })

    def _update_streak(self, habit, today):
        """Update habit streak"""
        yesterday = today - timedelta(days=1)
        yesterday_completed = habit.completions.filter(
            completion_date=yesterday, completed=True
        ).exists()
        
        if yesterday_completed or habit.current_streak == 0:
            habit.current_streak += 1
        else:
            habit.current_streak = 1
        
        if habit.current_streak > habit.longest_streak:
            habit.longest_streak = habit.current_streak
        
        habit.total_completions += 1
        habit.save(update_fields=['current_streak', 'longest_streak', 'total_completions'])
        
        # Update user stats
        user = habit.user
        user.total_habits_completed += 1
        if habit.current_streak > user.longest_streak:
            user.longest_streak = habit.current_streak
        user.save(update_fields=['total_habits_completed', 'longest_streak'])

    def _recalculate_streak(self, habit):
        """Recalculate streak after unchecking"""
        habit.current_streak = max(0, habit.current_streak - 1)
        habit.total_completions = max(0, habit.total_completions - 1)
        habit.save(update_fields=['current_streak', 'total_completions'])
        
        user = habit.user
        user.total_habits_completed = max(0, user.total_habits_completed - 1)
        user.save(update_fields=['total_habits_completed'])

    def _award_xp(self, habit, user):
        """Award XP to user"""
        user.xp_points += habit.xp_reward
        # Level up check
        new_level = (user.xp_points // 100) + 1
        user.level = new_level
        user.save(update_fields=['xp_points', 'level'])

    def _remove_xp(self, habit, user):
        """Remove XP when unchecking"""
        user.xp_points = max(0, user.xp_points - habit.xp_reward)
        user.level = max(1, (user.xp_points // 100) + 1)
        user.save(update_fields=['xp_points', 'level'])

    def _check_achievements(self, user):
        """Check and award achievements"""
        achievements_to_check = Achievement.objects.filter(is_active=True)
        
        for achievement in achievements_to_check:
            if user.user_achievements.filter(achievement=achievement).exists():
                continue
            
            unlocked = False
            
            if achievement.badge_type == 'streak':
                unlocked = user.habits.filter(
                    current_streak__gte=achievement.requirement_value
                ).exists()
            elif achievement.badge_type == 'completion':
                unlocked = user.total_habits_completed >= achievement.requirement_value
            elif achievement.badge_type == 'milestone':
                unlocked = user.habits.filter(is_active=True).count() >= achievement.requirement_value
            
            if unlocked:
                UserAchievement.objects.create(user=user, achievement=achievement)
                user.xp_points += achievement.xp_reward
                user.save(update_fields=['xp_points'])

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get completion history for a habit"""
        habit = self.get_object()
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        completions = habit.completions.filter(
            completion_date__gte=start_date
        ).order_by('completion_date')
        
        return Response(HabitCompletionSerializer(completions, many=True).data)

    @action(detail=False, methods=['get'])
    def by_routine(self, request):
        """Get habits grouped by routine"""
        habits = self.get_queryset()
        result = {}
        for routine_key, routine_label in Habit.ROUTINE_CHOICES:
            routine_habits = habits.filter(routine=routine_key)
            result[routine_key] = HabitSerializer(
                routine_habits, many=True, context={'request': request}
            ).data
        return Response(result)


class AnalyticsView(APIView):
    """Analytics and progress data"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = timezone.now().date()
        
        period = request.query_params.get('period', 'week')
        
        if period == 'week':
            start_date = today - timedelta(days=6)
            days_range = 7
        elif period == 'month':
            start_date = today - timedelta(days=29)
            days_range = 30
        else:
            start_date = today - timedelta(days=6)
            days_range = 7
        
        # Daily completion data for chart
        daily_data = []
        for i in range(days_range):
            day = start_date + timedelta(days=i)
            total = user.habits.filter(is_active=True).count()
            completed = HabitCompletion.objects.filter(
                habit__user=user,
                completion_date=day,
                completed=True
            ).count()
            rate = (completed / total * 100) if total > 0 else 0
            daily_data.append({
                'date': day.strftime('%Y-%m-%d'),
                'day': day.strftime('%a'),
                'completed': completed,
                'total': total,
                'rate': round(rate, 1),
            })
        
        # Per-habit stats
        habits = user.habits.filter(is_active=True)
        habit_stats = []
        for habit in habits:
            completions_in_period = habit.completions.filter(
                completion_date__gte=start_date, completed=True
            ).count()
            habit_stats.append({
                'id': str(habit.id),
                'title': habit.title,
                'icon': habit.icon,
                'color': habit.color,
                'streak': habit.current_streak,
                'completions': completions_in_period,
                'success_rate': habit.success_rate,
            })
        
        # Sort by success rate
        habit_stats.sort(key=lambda x: x['success_rate'], reverse=True)
        
        # Overall stats
        total_completions = HabitCompletion.objects.filter(
            habit__user=user,
            completion_date__gte=start_date,
            completed=True
        ).count()
        
        total_possible = habits.count() * days_range
        overall_rate = (total_completions / total_possible * 100) if total_possible > 0 else 0
        
        return Response({
            'period': period,
            'daily_data': daily_data,
            'habit_stats': habit_stats,
            'total_completions': total_completions,
            'overall_rate': round(overall_rate, 1),
            'productivity_score': user.productivity_score,
            'best_streak': habits.order_by('-longest_streak').first().longest_streak if habits.exists() else 0,
        })


class AchievementView(APIView):
    """User achievements"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        all_achievements = Achievement.objects.filter(is_active=True)
        user_achievements = user.user_achievements.values_list('achievement_id', flat=True)
        
        result = []
        for ach in all_achievements:
            data = AchievementSerializer(ach).data
            data['unlocked'] = ach.id in user_achievements
            if ach.id in user_achievements:
                ua = user.user_achievements.get(achievement=ach)
                data['unlocked_at'] = ua.unlocked_at
            result.append(data)
        
        return Response(result)


class GoalViewSet(viewsets.ModelViewSet):
    """CRUD for user goals"""
    serializer_class = GoalSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CalendarView(APIView):
    """Calendar data - completions per day in a month"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        year = int(request.query_params.get('year', timezone.now().year))
        month = int(request.query_params.get('month', timezone.now().month))
        
        from calendar import monthrange
        _, days_in_month = monthrange(year, month)
        
        start_date = date(year, month, 1)
        end_date = date(year, month, days_in_month)
        
        completions = HabitCompletion.objects.filter(
            habit__user=user,
            completion_date__range=[start_date, end_date],
        ).values('completion_date').annotate(
            completed_count=Count('id', filter=Q(completed=True)),
            total_count=Count('id')
        )
        
        calendar_data = {}
        for item in completions:
            day = item['completion_date'].day
            rate = (item['completed_count'] / item['total_count'] * 100) if item['total_count'] > 0 else 0
            calendar_data[day] = {
                'completed': item['completed_count'],
                'total': item['total_count'],
                'rate': round(rate, 1),
            }
        
        return Response({
            'year': year,
            'month': month,
            'days_in_month': days_in_month,
            'calendar': calendar_data,
        })

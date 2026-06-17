"""
HabitFlow Serializers
DRF serializers for all models
"""

from rest_framework import serializers
from django.utils import timezone
from .models import User, Category, Habit, HabitCompletion, Achievement, UserAchievement, Goal


class UserProfileSerializer(serializers.ModelSerializer):
    level_progress = serializers.ReadOnlyField()
    productivity_score = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar_url', 'bio', 'timezone', 'theme',
            'xp_points', 'level', 'total_habits_completed',
            'longest_streak', 'level_progress', 'productivity_score',
            'created_at',
        ]
        read_only_fields = ['id', 'xp_points', 'level', 'total_habits_completed', 'created_at']


class CategorySerializer(serializers.ModelSerializer):
    habit_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'icon', 'color', 'habit_count']
    
    def get_habit_count(self, obj):
        return obj.habit_set.filter(is_active=True).count()


class HabitCompletionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitCompletion
        fields = ['id', 'completion_date', 'completed', 'notes', 'mood', 'completed_at']
        read_only_fields = ['id', 'completed_at']


class HabitSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)
    is_completed_today = serializers.SerializerMethodField()
    success_rate = serializers.ReadOnlyField()
    xp_reward = serializers.ReadOnlyField()
    today_completion = serializers.SerializerMethodField()
    
    class Meta:
        model = Habit
        fields = [
            'id', 'title', 'description', 'icon', 'color',
            'category', 'category_detail',
            'difficulty', 'frequency', 'routine', 'custom_days',
            'reminder_time', 'reminder_enabled',
            'current_streak', 'longest_streak', 'total_completions',
            'is_active', 'created_at', 'updated_at',
            'is_completed_today', 'success_rate', 'xp_reward',
            'today_completion',
        ]
        read_only_fields = ['id', 'current_streak', 'longest_streak', 'total_completions', 'created_at']
    
    def get_is_completed_today(self, obj):
        return obj.is_completed_today()
    
    def get_today_completion(self, obj):
        today = timezone.now().date()
        try:
            completion = obj.completions.get(completion_date=today)
            return HabitCompletionSerializer(completion).data
        except HabitCompletion.DoesNotExist:
            return None


class HabitCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habit
        fields = [
            'title', 'description', 'icon', 'color',
            'category', 'difficulty', 'frequency', 'routine',
            'custom_days', 'reminder_time', 'reminder_enabled',
        ]
    
    def create(self, validated_data):
        user = self.context['request'].user
        return Habit.objects.create(user=user, **validated_data)


class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'title', 'description', 'badge_icon', 'badge_type', 'xp_reward', 'requirement_value']


class UserAchievementSerializer(serializers.ModelSerializer):
    achievement = AchievementSerializer(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = ['id', 'achievement', 'unlocked_at']


class GoalSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.ReadOnlyField()
    habit_title = serializers.SerializerMethodField()
    
    class Meta:
        model = Goal
        fields = [
            'id', 'habit', 'habit_title', 'title', 'description',
            'target_value', 'current_value', 'deadline',
            'status', 'progress_percentage', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_habit_title(self, obj):
        return obj.habit.title if obj.habit else None
    
    def create(self, validated_data):
        user = self.context['request'].user
        return Goal.objects.create(user=user, **validated_data)


class DashboardSerializer(serializers.Serializer):
    """Aggregated dashboard data"""
    user = UserProfileSerializer()
    today_habits = HabitSerializer(many=True)
    today_completion_rate = serializers.FloatField()
    weekly_completion_rate = serializers.FloatField()
    total_active_habits = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    recent_achievements = UserAchievementSerializer(many=True)
    motivational_quote = serializers.DictField()

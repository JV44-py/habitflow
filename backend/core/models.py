"""
HabitFlow Models
Complete database schema for habit tracking, gamification, and analytics
"""

from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    """Extended user model with profile data"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supabase_uid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    avatar_url = models.URLField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    timezone = models.CharField(max_length=50, default='UTC')
    theme = models.CharField(max_length=10, default='dark', choices=[('dark', 'Dark'), ('light', 'Light')])
    
    # Gamification
    xp_points = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    total_habits_completed = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.email or self.username

    @property
    def productivity_score(self):
        """Calculate productivity score 0-100"""
        if self.total_habits_completed == 0:
            return 0
        habits_count = self.habits.filter(is_active=True).count()
        if habits_count == 0:
            return 0
        # Score based on completion rate and streaks
        base_score = min(100, (self.total_habits_completed / max(1, habits_count * 30)) * 100)
        streak_bonus = min(20, self.longest_streak * 0.5)
        return min(100, int(base_score + streak_bonus))

    @property
    def level_progress(self):
        """XP needed for next level"""
        xp_for_next = self.level * 100
        current_level_xp = (self.level - 1) * 100
        progress = self.xp_points - current_level_xp
        return {
            'current_xp': self.xp_points,
            'level_xp': progress,
            'needed_xp': xp_for_next,
            'percentage': min(100, int((progress / xp_for_next) * 100))
        }


class Category(models.Model):
    """Habit categories"""
    CATEGORY_ICONS = [
        ('🏃', 'Fitness'),
        ('🧘', 'Mindfulness'),
        ('📚', 'Learning'),
        ('💧', 'Health'),
        ('😴', 'Sleep'),
        ('🍎', 'Nutrition'),
        ('💼', 'Work'),
        ('🎨', 'Creative'),
        ('👥', 'Social'),
        ('💰', 'Finance'),
        ('🌿', 'Nature'),
        ('⭐', 'Other'),
    ]
    
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=10, default='⭐')
    color = models.CharField(max_length=7, default='#6366f1')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Habit(models.Model):
    """Core habit model"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekdays', 'Weekdays'),
        ('weekends', 'Weekends'),
        ('custom', 'Custom'),
    ]

    ROUTINE_CHOICES = [
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
        ('anytime', 'Anytime'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habits')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    icon = models.CharField(max_length=10, default='✅')
    color = models.CharField(max_length=7, default='#6366f1')
    
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    frequency = models.CharField(max_length=10, choices=FREQUENCY_CHOICES, default='daily')
    routine = models.CharField(max_length=10, choices=ROUTINE_CHOICES, default='anytime')
    
    # Custom schedule (for 'custom' frequency)
    custom_days = models.JSONField(default=list, blank=True)  # [0,1,2,3,4] = Mon-Fri
    
    # Reminder
    reminder_time = models.TimeField(null=True, blank=True)
    reminder_enabled = models.BooleanField(default=False)
    
    # Tracking
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    total_completions = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # XP reward per completion
    @property
    def xp_reward(self):
        rewards = {'easy': 10, 'medium': 20, 'hard': 35}
        return rewards.get(self.difficulty, 20)

    class Meta:
        db_table = 'habits'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def is_completed_today(self):
        today = timezone.now().date()
        return self.completions.filter(completion_date=today, completed=True).exists()

    @property
    def success_rate(self):
        """Calculate success rate over last 30 days"""
        thirty_days_ago = timezone.now().date() - timezone.timedelta(days=30)
        total = self.completions.filter(completion_date__gte=thirty_days_ago).count()
        if total == 0:
            return 0
        completed = self.completions.filter(
            completion_date__gte=thirty_days_ago, completed=True
        ).count()
        return int((completed / total) * 100)


class HabitCompletion(models.Model):
    """Daily completion records"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='completions')
    completion_date = models.DateField(default=timezone.now)
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    mood = models.IntegerField(null=True, blank=True, choices=[(i, i) for i in range(1, 6)])  # 1-5 mood rating
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'habit_completions'
        unique_together = ['habit', 'completion_date']
        ordering = ['-completion_date']

    def __str__(self):
        status = "✅" if self.completed else "❌"
        return f"{status} {self.habit.title} - {self.completion_date}"

    def save(self, *args, **kwargs):
        if self.completed and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)


class Achievement(models.Model):
    """Achievement/Badge definitions"""
    BADGE_TYPES = [
        ('streak', 'Streak'),
        ('completion', 'Completion'),
        ('consistency', 'Consistency'),
        ('milestone', 'Milestone'),
        ('special', 'Special'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.TextField()
    badge_icon = models.CharField(max_length=10)
    badge_type = models.CharField(max_length=20, choices=BADGE_TYPES)
    xp_reward = models.IntegerField(default=50)
    requirement_value = models.IntegerField(default=1)  # Threshold to unlock
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'achievements'

    def __str__(self):
        return self.title


class UserAchievement(models.Model):
    """User-specific achievement unlocks"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_achievements'
        unique_together = ['user', 'achievement']

    def __str__(self):
        return f"{self.user.username} - {self.achievement.title}"


class Goal(models.Model):
    """User goals tied to habits"""
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name='goals', null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_value = models.IntegerField(default=30)  # e.g., 30 days
    current_value = models.IntegerField(default=0)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'goals'

    @property
    def progress_percentage(self):
        if self.target_value == 0:
            return 0
        return min(100, int((self.current_value / self.target_value) * 100))

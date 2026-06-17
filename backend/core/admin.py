from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Category, Habit, HabitCompletion, Achievement, UserAchievement, Goal


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('username', 'email', 'level', 'xp_points', 'total_habits_completed', 'is_staff')
    list_filter   = ('is_staff', 'is_active', 'level')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets     = BaseUserAdmin.fieldsets + (
        ('HabitFlow Profile', {'fields': (
            'supabase_uid', 'avatar_url', 'bio', 'timezone', 'theme',
            'xp_points', 'level', 'total_habits_completed', 'longest_streak',
        )}),
    )
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('name', 'icon', 'color', 'user', 'is_default')
    list_filter   = ('is_default',)
    search_fields = ('name',)


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display  = ('title', 'user', 'category', 'difficulty', 'routine', 'current_streak', 'is_active')
    list_filter   = ('difficulty', 'routine', 'frequency', 'is_active')
    search_fields = ('title', 'user__username')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields   = ('user',)


@admin.register(HabitCompletion)
class HabitCompletionAdmin(admin.ModelAdmin):
    list_display  = ('habit', 'completion_date', 'completed', 'mood')
    list_filter   = ('completed', 'completion_date')
    search_fields = ('habit__title',)
    date_hierarchy = 'completion_date'


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display  = ('title', 'badge_icon', 'badge_type', 'xp_reward', 'requirement_value', 'is_active')
    list_filter   = ('badge_type', 'is_active')
    search_fields = ('title',)


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display  = ('user', 'achievement', 'unlocked_at')
    list_filter   = ('unlocked_at',)
    search_fields = ('user__username', 'achievement__title')
    raw_id_fields  = ('user',)


@admin.register(Goal)
class GoalAdmin(admin.ModelAdmin):
    list_display  = ('title', 'user', 'status', 'target_value', 'current_value', 'deadline')
    list_filter   = ('status',)
    search_fields = ('title', 'user__username')
    raw_id_fields  = ('user',)

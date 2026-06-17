"""
Supabase JWT Authentication for Django REST Framework
Validates Supabase JWT tokens and maps to Django users
"""

import os
import requests
import logging
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

logger = logging.getLogger(__name__)
User = get_user_model()


class SupabaseAuthentication(BaseAuthentication):
    """
    Authenticate requests using Supabase JWT tokens.
    
    Clients should authenticate by passing the token in the 
    Authorization header: "Authorization: Bearer <token>"
    """

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        if not token:
            return None
        
        try:
            user_data = self.verify_supabase_token(token)
            user = self.get_or_create_user(user_data)
            return (user, token)
        except Exception as e:
            logger.warning(f"Authentication failed: {e}")
            raise AuthenticationFailed(str(e))

    def verify_supabase_token(self, token):
        """Verify token with Supabase and get user info"""
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            raise AuthenticationFailed('Supabase not configured')
        
        response = requests.get(
            f"{supabase_url}/auth/v1/user",
            headers={
                'Authorization': f'Bearer {token}',
                'apikey': supabase_key,
            },
            timeout=10
        )
        
        if response.status_code != 200:
            raise AuthenticationFailed('Invalid or expired token')
        
        return response.json()

    def get_or_create_user(self, user_data):
        """Get existing user or create new one from Supabase data"""
        supabase_uid = user_data.get('id')
        email = user_data.get('email', '')
        
        if not supabase_uid:
            raise AuthenticationFailed('Invalid user data from Supabase')
        
        try:
            user = User.objects.get(supabase_uid=supabase_uid)
            # Update email if changed
            if user.email != email:
                user.email = email
                user.save(update_fields=['email'])
        except User.DoesNotExist:
            # Create new user
            user_metadata = user_data.get('user_metadata', {})
            username = email.split('@')[0] if email else supabase_uid[:8]
            
            # Make username unique
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                supabase_uid=supabase_uid,
                first_name=user_metadata.get('first_name', ''),
                last_name=user_metadata.get('last_name', ''),
            )
            
            # Set up default categories for new user
            self.setup_default_categories(user)
        
        return user

    def setup_default_categories(self, user):
        """Create default habit categories for new users"""
        from core.models import Category
        
        defaults = [
            {'name': 'Health & Fitness', 'icon': '🏃', 'color': '#10b981'},
            {'name': 'Mindfulness', 'icon': '🧘', 'color': '#8b5cf6'},
            {'name': 'Learning', 'icon': '📚', 'color': '#3b82f6'},
            {'name': 'Nutrition', 'icon': '🍎', 'color': '#f59e0b'},
            {'name': 'Sleep', 'icon': '😴', 'color': '#6366f1'},
            {'name': 'Work', 'icon': '💼', 'color': '#64748b'},
        ]
        
        for cat_data in defaults:
            Category.objects.get_or_create(
                user=user,
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                }
            )

from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.contrib.auth.models import User
from django.conf import settings
import json


class Command(BaseCommand):
    help = 'Debug cache issues and clear user-specific cache entries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-user-cache',
            type=int,
            help='Clear cache for specific user ID',
        )
        parser.add_argument(
            '--clear-all-user-cache',
            action='store_true',
            help='Clear all user-specific cache entries',
        )
        parser.add_argument(
            '--list-cache-keys',
            action='store_true',
            help='List all cache keys (if supported by cache backend)',
        )
        parser.add_argument(
            '--clear-all-cache',
            action='store_true',
            help='Clear entire cache',
        )

    def handle(self, *args, **options):
        if options['clear_user_cache']:
            user_id = options['clear_user_cache']
            self.clear_user_cache(user_id)
        
        elif options['clear_all_user_cache']:
            self.clear_all_user_cache()
        
        elif options['list_cache_keys']:
            self.list_cache_keys()
        
        elif options['clear_all_cache']:
            self.clear_all_cache()
        
        else:
            self.stdout.write(
                self.style.WARNING(
                    'No action specified. Use --help to see available options.'
                )
            )

    def clear_user_cache(self, user_id):
        """Clear cache entries for a specific user"""
        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f"Clearing cache for user: {user.username} (ID: {user_id})")
            
            # Since we're using database cache, we'll clear the entire cache
            # In a production environment with Redis, you could use pattern matching
            cache.clear()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Cache cleared for user {user.username}. '
                    'Note: Entire cache was cleared due to database cache backend limitations.'
                )
            )
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'User with ID {user_id} does not exist')
            )

    def clear_all_user_cache(self):
        """Clear all user-specific cache entries"""
        self.stdout.write("Clearing all user-specific cache entries...")
        cache.clear()
        self.stdout.write(
            self.style.SUCCESS(
                'All user-specific cache entries cleared. '
                'Note: Entire cache was cleared due to database cache backend limitations.'
            )
        )

    def list_cache_keys(self):
        """List cache keys (limited support with database cache)"""
        self.stdout.write(
            self.style.WARNING(
                'Cache key listing is not supported with database cache backend. '
                'Consider using Redis for better cache debugging capabilities.'
            )
        )

    def clear_all_cache(self):
        """Clear entire cache"""
        self.stdout.write("Clearing entire cache...")
        cache.clear()
        self.stdout.write(
            self.style.SUCCESS('Entire cache cleared successfully')
        )

    def get_cache_stats(self):
        """Get cache statistics"""
        self.stdout.write("Cache Configuration:")
        self.stdout.write(f"  Backend: {settings.CACHES['default']['BACKEND']}")
        self.stdout.write(f"  Location: {settings.CACHES['default']['LOCATION']}")
        
        # Try to get some basic cache info
        try:
            # Test cache functionality
            test_key = 'cache_debug_test'
            cache.set(test_key, 'test_value', 60)
            test_result = cache.get(test_key)
            cache.delete(test_key)
            
            if test_result == 'test_value':
                self.stdout.write(
                    self.style.SUCCESS('Cache is functioning correctly')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Cache test failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Cache test error: {str(e)}')
            )
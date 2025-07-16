from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Set up cache backend for development or production'

    def handle(self, *args, **options):
        cache_backend = settings.CACHES['default']['BACKEND']
        
        if 'redis' in cache_backend.lower():
            self.stdout.write('Redis cache backend detected.')
            self.setup_redis_cache()
        elif 'db' in cache_backend.lower():
            self.stdout.write('Database cache backend detected.')
            self.setup_database_cache()
        else:
            self.stdout.write(
                self.style.WARNING(f'Unknown cache backend: {cache_backend}')
            )
            return
        
        # Test cache functionality
        self.test_cache()
        
        self.stdout.write(
            self.style.SUCCESS('Cache setup completed successfully!')
        )
    
    def setup_redis_cache(self):
        """Setup Redis cache for production"""
        try:
            # Test Redis connection
            cache.set('test_redis', 'working', 10)
            result = cache.get('test_redis')
            
            if result == 'working':
                self.stdout.write(
                    self.style.SUCCESS('✅ Redis connection successful')
                )
                cache.delete('test_redis')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Redis connection failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Redis setup error: {e}')
            )
    
    def setup_database_cache(self):
        """Setup database cache for development"""
        try:
            # Create cache table
            self.stdout.write('Creating database cache table...')
            call_command('createcachetable', verbosity=0)
            
            # Test database cache
            cache.set('test_db_cache', 'working', 10)
            result = cache.get('test_db_cache')
            
            if result == 'working':
                self.stdout.write(
                    self.style.SUCCESS('✅ Database cache setup successful')
                )
                cache.delete('test_db_cache')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Database cache setup failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Database cache setup error: {e}')
            )
    
    def test_cache(self):
        """Test basic cache functionality"""
        try:
            test_key = 'cache_test_key'
            test_value = 'cache_test_value'
            
            # Set and get test
            cache.set(test_key, test_value, 30)
            retrieved_value = cache.get(test_key)
            
            if retrieved_value == test_value:
                self.stdout.write('✅ Cache read/write test passed')
                cache.delete(test_key)
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ Cache read/write test failed')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Cache test error: {e}')
            )
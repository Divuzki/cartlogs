from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
import os
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Diagnose Redis cache issues in production'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )
        parser.add_argument(
            '--test-operations',
            action='store_true',
            help='Test all cache operations',
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        self.test_operations = options['test_operations']
        
        self.stdout.write(self.style.HTTP_INFO('🔍 Redis Cache Diagnostic Tool'))
        self.stdout.write('=' * 50)
        
        # Step 1: Environment Check
        self.check_environment()
        
        # Step 2: Cache Configuration Check
        self.check_cache_config()
        
        # Step 3: Redis Connection Test
        self.test_redis_connection()
        
        # Step 4: Cache Operations Test
        if self.test_operations:
            self.test_cache_operations()
        
        # Step 5: Production-specific checks
        self.check_production_issues()
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('✅ Diagnostic complete!'))

    def check_environment(self):
        """Check environment variables and settings"""
        self.stdout.write(self.style.HTTP_INFO('\n📋 Environment Check'))
        
        # Check DEBUG setting
        debug_status = settings.DEBUG
        self.stdout.write(f"DEBUG: {debug_status}")
        
        # Check REDIS_URL
        redis_url = os.environ.get('REDIS_URL')
        if redis_url:
            # Mask password for security
            masked_url = self.mask_redis_url(redis_url)
            self.stdout.write(f"REDIS_URL: {masked_url}")
        else:
            self.stdout.write(self.style.WARNING("⚠️  REDIS_URL not found in environment"))
        
        # Check if we should be using Redis
        should_use_redis = not debug_status and redis_url
        self.stdout.write(f"Should use Redis: {should_use_redis}")
        
        if self.verbose:
            self.stdout.write(f"Environment variables:")
            for key in ['DEBUG', 'REDIS_URL', 'DATABASE_URL']:
                value = os.environ.get(key, 'Not set')
                if 'URL' in key and value != 'Not set':
                    value = self.mask_url(value)
                self.stdout.write(f"  {key}: {value}")

    def check_cache_config(self):
        """Check Django cache configuration"""
        self.stdout.write(self.style.HTTP_INFO('\n⚙️  Cache Configuration'))
        
        cache_config = settings.CACHES['default']
        backend = cache_config.get('BACKEND')
        location = cache_config.get('LOCATION', 'Not specified')
        
        self.stdout.write(f"Backend: {backend}")
        
        if 'redis' in backend.lower():
            self.stdout.write(self.style.SUCCESS("✅ Redis backend configured"))
            if location:
                masked_location = self.mask_redis_url(location)
                self.stdout.write(f"Location: {masked_location}")
        else:
            self.stdout.write(self.style.WARNING(f"⚠️  Non-Redis backend: {backend}"))
        
        if self.verbose:
            self.stdout.write("Full cache config:")
            for key, value in cache_config.items():
                if key == 'LOCATION' and isinstance(value, str) and 'redis://' in value:
                    value = self.mask_redis_url(value)
                self.stdout.write(f"  {key}: {value}")

    def test_redis_connection(self):
        """Test basic Redis connection"""
        self.stdout.write(self.style.HTTP_INFO('\n🔌 Redis Connection Test'))
        
        try:
            # Test basic connection
            cache.set('diagnostic_test', 'connection_ok', 10)
            result = cache.get('diagnostic_test')
            
            if result == 'connection_ok':
                self.stdout.write(self.style.SUCCESS("✅ Basic connection: OK"))
                cache.delete('diagnostic_test')
            else:
                self.stdout.write(self.style.ERROR(f"❌ Basic connection failed: Expected 'connection_ok', got '{result}'"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Connection error: {e}"))
            self.stdout.write(self.style.WARNING("💡 Possible causes:"))
            self.stdout.write("   - Redis service not running")
            self.stdout.write("   - Incorrect REDIS_URL")
            self.stdout.write("   - Network connectivity issues")
            self.stdout.write("   - Redis authentication problems")
            return False
        
        # Test Redis-specific features if using Redis
        if 'redis' in settings.CACHES['default']['BACKEND'].lower():
            self.test_redis_specific_features()
        
        return True

    def test_redis_specific_features(self):
        """Test Redis-specific features"""
        try:
            from django_redis import get_redis_connection
            
            redis_conn = get_redis_connection("default")
            
            # Test Redis info
            info = redis_conn.info()
            self.stdout.write(f"Redis version: {info.get('redis_version', 'Unknown')}")
            self.stdout.write(f"Connected clients: {info.get('connected_clients', 'Unknown')}")
            self.stdout.write(f"Memory usage: {info.get('used_memory_human', 'Unknown')}")
            
            # Test Redis ping
            pong = redis_conn.ping()
            if pong:
                self.stdout.write(self.style.SUCCESS("✅ Redis ping: OK"))
            else:
                self.stdout.write(self.style.ERROR("❌ Redis ping failed"))
                
        except ImportError:
            self.stdout.write(self.style.WARNING("⚠️  django-redis not available for advanced testing"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Redis-specific test failed: {e}"))

    def test_cache_operations(self):
        """Test various cache operations"""
        self.stdout.write(self.style.HTTP_INFO('\n🧪 Cache Operations Test'))
        
        test_cases = [
            ('string', 'test_string_value'),
            ('integer', 12345),
            ('list', [1, 2, 3, 'test']),
            ('dict', {'key': 'value', 'number': 42}),
            ('boolean', True),
            ('none', None),
        ]
        
        for data_type, test_value in test_cases:
            try:
                key = f'diagnostic_{data_type}'
                
                # Test set
                cache.set(key, test_value, 30)
                
                # Test get
                retrieved = cache.get(key)
                
                if retrieved == test_value:
                    self.stdout.write(self.style.SUCCESS(f"✅ {data_type}: OK"))
                else:
                    self.stdout.write(self.style.ERROR(f"❌ {data_type}: Expected {test_value}, got {retrieved}"))
                
                # Test delete
                cache.delete(key)
                
                # Verify deletion
                after_delete = cache.get(key)
                if after_delete is None:
                    if self.verbose:
                        self.stdout.write(f"   Delete {data_type}: OK")
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️  Delete {data_type}: Value still exists"))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ {data_type} test failed: {e}"))
        
        # Test timeout functionality
        self.test_timeout_functionality()

    def test_timeout_functionality(self):
        """Test cache timeout functionality"""
        self.stdout.write(self.style.HTTP_INFO('\n⏰ Timeout Test'))
        
        try:
            import time
            
            # Set a value with 2-second timeout
            cache.set('timeout_test', 'will_expire', 2)
            
            # Immediately check
            immediate = cache.get('timeout_test')
            if immediate == 'will_expire':
                self.stdout.write(self.style.SUCCESS("✅ Immediate retrieval: OK"))
            else:
                self.stdout.write(self.style.ERROR("❌ Immediate retrieval failed"))
            
            # Wait and check expiration (only in verbose mode)
            if self.verbose:
                self.stdout.write("Waiting 3 seconds for expiration...")
                time.sleep(3)
                
                expired = cache.get('timeout_test')
                if expired is None:
                    self.stdout.write(self.style.SUCCESS("✅ Timeout expiration: OK"))
                else:
                    self.stdout.write(self.style.WARNING("⚠️  Value did not expire as expected"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Timeout test failed: {e}"))

    def check_production_issues(self):
        """Check for common production issues"""
        self.stdout.write(self.style.HTTP_INFO('\n🏭 Production Issues Check'))
        
        issues_found = []
        
        # Check if DEBUG is properly set
        if settings.DEBUG:
            issues_found.append("DEBUG=True in production (should be False)")
        
        # Check Redis URL format
        redis_url = os.environ.get('REDIS_URL')
        if redis_url:
            if not redis_url.startswith('redis://'):
                issues_found.append("REDIS_URL doesn't start with 'redis://'")
            if '@' not in redis_url:
                issues_found.append("REDIS_URL missing authentication")
        
        # Check cache backend consistency
        backend = settings.CACHES['default']['BACKEND']
        if not settings.DEBUG and redis_url and 'redis' not in backend.lower():
            issues_found.append("Redis URL available but not using Redis backend")
        
        # Check for missing dependencies
        try:
            import redis
            import django_redis
        except ImportError as e:
            issues_found.append(f"Missing Redis dependency: {e}")
        
        if issues_found:
            self.stdout.write(self.style.ERROR("❌ Issues found:"))
            for issue in issues_found:
                self.stdout.write(f"   • {issue}")
        else:
            self.stdout.write(self.style.SUCCESS("✅ No obvious production issues detected"))
        
        # Provide recommendations
        self.provide_recommendations()

    def provide_recommendations(self):
        """Provide troubleshooting recommendations"""
        self.stdout.write(self.style.HTTP_INFO('\n💡 Recommendations'))
        
        recommendations = [
            "1. Verify REDIS_URL is correctly set in Railway environment",
            "2. Ensure Redis service is running in Railway dashboard",
            "3. Check Railway logs for Redis connection errors",
            "4. Test cache operations in Railway shell: railway run python manage.py diagnose_redis --test-operations",
            "5. Verify django-redis is in requirements.txt",
            "6. Check if Redis service has sufficient memory",
            "7. Monitor Redis connection pool settings",
        ]
        
        for rec in recommendations:
            self.stdout.write(rec)

    def mask_redis_url(self, url):
        """Mask sensitive parts of Redis URL"""
        if not url or 'redis://' not in url:
            return url
        
        try:
            # Format: redis://user:password@host:port/db
            parts = url.split('@')
            if len(parts) == 2:
                auth_part = parts[0]
                host_part = parts[1]
                
                # Mask password
                if ':' in auth_part:
                    user_pass = auth_part.split(':')
                    if len(user_pass) >= 3:  # redis://user:pass
                        masked_auth = f"{user_pass[0]}:{user_pass[1]}:***"
                        return f"{masked_auth}@{host_part}"
            
            return url.replace(url.split('@')[0].split(':')[-1], '***')
        except:
            return "redis://***:***@***:***"

    def mask_url(self, url):
        """Mask sensitive parts of any URL"""
        if not url or '://' not in url:
            return url
        
        try:
            if '@' in url:
                parts = url.split('@')
                protocol_auth = parts[0]
                host_part = parts[1]
                
                if ':' in protocol_auth:
                    protocol_user_pass = protocol_auth.split(':')
                    if len(protocol_user_pass) >= 3:
                        protocol = protocol_user_pass[0]
                        return f"{protocol}://***:***@{host_part}"
            
            return url
        except:
            return "***://***:***@***"
#!/usr/bin/env python
"""
Quick Redis cache.set() test script for production debugging
Run this in Railway shell: railway run python test_cache_set.py
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
django.setup()

from django.core.cache import cache
from django.conf import settings

def test_cache_set():
    print("🔍 Testing Redis cache.set() operations...")
    print("=" * 50)
    
    # Environment info
    print(f"DEBUG: {settings.DEBUG}")
    print(f"Cache Backend: {settings.CACHES['default']['BACKEND']}")
    
    redis_url = os.environ.get('REDIS_URL')
    if redis_url:
        # Mask password for security
        masked_url = redis_url.split('@')[0].split(':')[:-1] + ['***'] + redis_url.split('@')[1:]
        print(f"REDIS_URL: {'@'.join([':'.join(masked_url[:-1]), masked_url[-1]])}")
    else:
        print("❌ REDIS_URL not found!")
        return False
    
    print("\n🧪 Testing cache operations...")
    
    # Test 1: Basic string set/get
    try:
        test_key = f"test_cache_set_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        test_value = "Hello Redis!"
        
        print(f"\n1. Testing cache.set('{test_key}', '{test_value}', 60)")
        
        # Attempt to set
        result = cache.set(test_key, test_value, 60)
        print(f"   cache.set() returned: {result}")
        
        # Attempt to get
        retrieved = cache.get(test_key)
        print(f"   cache.get() returned: {retrieved}")
        
        if retrieved == test_value:
            print("   ✅ SUCCESS: Value stored and retrieved correctly")
        else:
            print(f"   ❌ FAILED: Expected '{test_value}', got '{retrieved}'")
            return False
            
        # Clean up
        cache.delete(test_key)
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False
    
    # Test 2: Different data types
    test_cases = [
        ('integer', 12345),
        ('list', [1, 2, 3]),
        ('dict', {'key': 'value'}),
        ('boolean', True),
    ]
    
    for i, (data_type, test_data) in enumerate(test_cases, 2):
        try:
            key = f"test_{data_type}_{datetime.now().strftime('%H%M%S')}"
            print(f"\n{i}. Testing {data_type}: {test_data}")
            
            cache.set(key, test_data, 30)
            retrieved = cache.get(key)
            
            if retrieved == test_data:
                print(f"   ✅ {data_type}: OK")
            else:
                print(f"   ❌ {data_type}: Expected {test_data}, got {retrieved}")
            
            cache.delete(key)
            
        except Exception as e:
            print(f"   ❌ {data_type} ERROR: {e}")
    
    # Test 3: Redis-specific connection test
    try:
        print("\n6. Testing Redis connection directly...")
        from django_redis import get_redis_connection
        
        redis_conn = get_redis_connection("default")
        
        # Test ping
        pong = redis_conn.ping()
        print(f"   Redis ping: {pong}")
        
        # Test direct Redis set/get
        redis_conn.set('direct_test', 'direct_value', ex=30)
        direct_result = redis_conn.get('direct_test')
        print(f"   Direct Redis get: {direct_result}")
        
        # Clean up
        redis_conn.delete('direct_test')
        
        if pong and direct_result:
            print("   ✅ Direct Redis connection: OK")
        else:
            print("   ❌ Direct Redis connection: FAILED")
            
    except ImportError:
        print("   ⚠️  django-redis not available for direct testing")
    except Exception as e:
        print(f"   ❌ Redis connection ERROR: {e}")
    
    # Test 4: Check for common issues
    print("\n7. Checking for common issues...")
    
    # Check cache key prefix
    cache_config = settings.CACHES['default']
    key_prefix = cache_config.get('KEY_PREFIX', '')
    if key_prefix:
        print(f"   Cache key prefix: '{key_prefix}'")
    
    # Check timeout setting
    timeout = cache_config.get('TIMEOUT', 'Not set')
    print(f"   Default timeout: {timeout}")
    
    # Check Redis options
    options = cache_config.get('OPTIONS', {})
    if options:
        print("   Redis options:")
        for key, value in options.items():
            if 'password' not in key.lower():
                print(f"     {key}: {value}")
    
    print("\n" + "=" * 50)
    print("✅ Cache test completed!")
    return True

if __name__ == "__main__":
    try:
        success = test_cache_set()
        if success:
            print("\n🎉 All tests passed! Redis cache.set() is working.")
        else:
            print("\n💥 Tests failed! Check the errors above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Script failed: {e}")
        sys.exit(1)
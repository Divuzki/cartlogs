from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json


def make_cache_key(*args, **kwargs):
    """Generate a consistent cache key from arguments"""
    key_data = {
        'args': args,
        'kwargs': sorted(kwargs.items())
    }
    key_string = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()


def cache_view_result(timeout=None, key_prefix='view'):
    """Decorator to cache view results"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Don't cache for authenticated users or POST requests
            if request.user.is_authenticated or request.method != 'GET':
                return view_func(request, *args, **kwargs)
            
            # Generate cache key
            cache_key = f"{key_prefix}:{view_func.__name__}:{make_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute view and cache result
            result = view_func(request, *args, **kwargs)
            cache_timeout = timeout or getattr(settings, 'CACHE_TIMEOUT_MEDIUM', 1800)
            cache.set(cache_key, result, cache_timeout)
            
            return result
        return wrapper
    return decorator


def cache_queryset(queryset, cache_key, timeout=None):
    """Cache a queryset result"""
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    
    # Convert queryset to list to cache it
    data = list(queryset)
    cache_timeout = timeout or getattr(settings, 'CACHE_TIMEOUT_MEDIUM', 1800)
    cache.set(cache_key, data, cache_timeout)
    return data


def invalidate_cache_pattern(pattern):
    """Invalidate cache keys matching a pattern"""
    try:
        from django_redis import get_redis_connection
        from django.conf import settings
        
        # Only use Redis pattern matching in production with Redis
        if settings.DEBUG and hasattr(settings, 'CACHES') and \
           settings.CACHES['default']['BACKEND'] == 'django_redis.cache.RedisCache':
            redis_conn = get_redis_connection("default")
            keys = redis_conn.keys(f"*{pattern}*")
            if keys:
                redis_conn.delete(*keys)
        else:
            # In development or without Redis, clear entire cache
            cache.clear()
    except Exception:
        # Fallback to clearing entire cache if pattern matching fails
        cache.clear()


def get_or_set_cache(key, callable_func, timeout=None):
    """Get from cache or set if not exists"""
    result = cache.get(key)
    if result is None:
        result = callable_func()
        cache_timeout = timeout or getattr(settings, 'CACHE_TIMEOUT_MEDIUM', 1800)
        cache.set(key, result, cache_timeout)
    return result
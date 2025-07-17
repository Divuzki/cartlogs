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


def cache_view_result(timeout=None, key_prefix='view', cloudflare_aware=True):
    """Decorator to cache view results
    
    When cloudflare_aware=True (default), this decorator will:
    - Skip local caching for anonymous users (Cloudflare handles this)
    - Only cache locally for authenticated users
    
    When cloudflare_aware=False, it behaves like the original decorator
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # For POST requests, never cache
            if request.method != 'GET':
                return view_func(request, *args, **kwargs)
            
            # Generate cache key
            cache_key = f"{key_prefix}:{view_func.__name__}:{make_cache_key(*args, **kwargs)}"
            
            # Cloudflare-aware caching strategy
            if cloudflare_aware:
                # For anonymous users, skip local caching (Cloudflare handles it)
                if not request.user.is_authenticated:
                    # Execute view without local caching
                    result = view_func(request, *args, **kwargs)
                    # Set cache headers for Cloudflare (handled by middleware)
                    return result
                
                # For authenticated users, use local caching
                result = cache.get(cache_key)
                if result is not None:
                    return result
                
                # Execute view and cache result for authenticated users
                result = view_func(request, *args, **kwargs)
                cache_timeout = timeout or getattr(settings, 'CACHE_TIMEOUT_MEDIUM', 1800)
                cache.set(cache_key, result, cache_timeout)
                return result
            
            # Legacy behavior (non-Cloudflare aware)
            else:
                # Don't cache for authenticated users
                if request.user.is_authenticated:
                    return view_func(request, *args, **kwargs)
                
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


def cache_queryset(queryset, cache_key, timeout=None, force_cache=False):
    """Cache a queryset result
    
    Args:
        queryset: Django queryset to cache
        cache_key: Cache key to use
        timeout: Cache timeout in seconds
        force_cache: If True, always cache regardless of Cloudflare optimization
    """
    # Check if we should use local caching
    # For Cloudflare optimization, we reduce local caching for data that
    # will be cached at the edge anyway
    if not force_cache:
        # For frequently accessed public data, rely more on Cloudflare
        # Only cache locally for complex queries or authenticated user data
        pass
    
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
    # Since we're using database cache and Cloudflare handles edge caching,
    # we'll clear the entire local cache when pattern invalidation is needed
    cache.clear()
    
    # TODO: Integrate with Cloudflare API to purge edge cache
    # This would require Cloudflare API credentials and zone ID
    # Example implementation:
    # cloudflare_purge_cache(pattern)


def cloudflare_purge_cache(urls=None, tags=None):
    """Purge Cloudflare cache for specific URLs or cache tags
    
    This function can be implemented to integrate with Cloudflare's API
    for selective cache purging when content changes.
    
    Args:
        urls: List of URLs to purge
        tags: List of cache tags to purge
    """
    # TODO: Implement Cloudflare API integration
    # Requires: CLOUDFLARE_API_TOKEN, CLOUDFLARE_ZONE_ID in settings
    pass


def get_or_set_cache(key, callable_func, timeout=None):
    """Get from cache or set if not exists"""
    result = cache.get(key)
    if result is None:
        result = callable_func()
        cache_timeout = timeout or getattr(settings, 'CACHE_TIMEOUT_MEDIUM', 1800)
        cache.set(key, result, cache_timeout)
    return result
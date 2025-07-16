from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.views.decorators.http import require_GET
import json

try:
    from django_redis import get_redis_connection
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


@staff_member_required
@require_GET
def cache_stats(request):
    """View to check cache statistics - only for staff members"""
    from django.conf import settings
    
    cache_backend = settings.CACHES['default']['BACKEND']
    is_redis = 'redis' in cache_backend.lower()
    
    stats = {
        'redis_available': REDIS_AVAILABLE and is_redis,
        'cache_backend': cache_backend,
        'environment': 'production' if settings.DEBUG else 'development',
    }
    
    if REDIS_AVAILABLE and is_redis:
        try:
            redis_conn = get_redis_connection("default")
            info = redis_conn.info()
            
            stats.update({
                'cache_hits': info.get('keyspace_hits', 0),
                'cache_misses': info.get('keyspace_misses', 0),
                'memory_usage': info.get('used_memory_human', 'N/A'),
                'connected_clients': info.get('connected_clients', 0),
                'total_keys': len(redis_conn.keys('*')),
                'uptime_seconds': info.get('uptime_in_seconds', 0),
            })
            
            # Calculate hit rate
            hits = stats['cache_hits']
            misses = stats['cache_misses']
            total_requests = hits + misses
            hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0
            stats['hit_rate_percentage'] = round(hit_rate, 2)
            
        except Exception as e:
            stats['error'] = str(e)
    else:
        stats['note'] = 'Using database cache - limited statistics available'
    
    return JsonResponse(stats, json_dumps_params={'indent': 2})


@staff_member_required
@require_GET
def cache_keys(request):
    """View to list all cache keys - only for staff members"""
    from django.conf import settings
    
    cache_backend = settings.CACHES['default']['BACKEND']
    is_redis = 'redis' in cache_backend.lower()
    
    if not REDIS_AVAILABLE or not is_redis:
        return JsonResponse({
            'error': 'Redis not available or not configured',
            'cache_backend': cache_backend,
            'note': 'Key listing only available with Redis cache backend'
        }, status=400)
    
    try:
        redis_conn = get_redis_connection("default")
        keys = [key.decode('utf-8') if isinstance(key, bytes) else key 
                for key in redis_conn.keys('*')]
        
        return JsonResponse({
            'total_keys': len(keys),
            'keys': sorted(keys)[:100],  # Limit to first 100 keys
            'note': 'Showing first 100 keys only' if len(keys) > 100 else 'All keys shown'
        }, json_dumps_params={'indent': 2})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@staff_member_required
@require_GET
def clear_cache(request):
    """View to clear all cache - only for staff members"""
    try:
        cache.clear()
        return JsonResponse({
            'status': 'success',
            'message': 'Cache cleared successfully'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
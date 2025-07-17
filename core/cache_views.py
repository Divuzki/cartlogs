from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.views.decorators.http import require_GET
import json


@staff_member_required
@require_GET
def cache_stats(request):
    """View to check cache statistics - only for staff members"""
    from django.conf import settings
    
    cache_backend = settings.CACHES['default']['BACKEND']
    
    stats = {
        'cache_backend': cache_backend,
        'environment': 'production' if not settings.DEBUG else 'development',
        'note': 'Using database cache - Cloudflare handles edge caching'
    }
    
    return JsonResponse(stats, json_dumps_params={'indent': 2})


@staff_member_required
@require_GET
def cache_keys(request):
    """View to list all cache keys - only for staff members"""
    from django.conf import settings
    
    cache_backend = settings.CACHES['default']['BACKEND']
    
    return JsonResponse({
        'cache_backend': cache_backend,
        'note': 'Key listing not available with database cache - using Cloudflare for edge caching'
    }, status=200)


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
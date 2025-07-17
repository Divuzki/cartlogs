from django.utils.cache import patch_cache_control
from django.http import HttpResponse
from django.conf import settings


class CloudflareCacheMiddleware:
    """
    Middleware to set appropriate cache headers for Cloudflare optimization.
    This works in conjunction with Cloudflare's Cache Rules to provide
    optimal caching behavior for both anonymous and authenticated users.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Only process GET requests
        if request.method != 'GET':
            return response
        
        # Don't cache for authenticated users
        if request.user.is_authenticated:
            patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True)
            response['CF-Cache-Status'] = 'BYPASS'
            return response
        
        # Set cache headers for anonymous users based on URL patterns
        path = request.path
        
        if self._is_static_asset(path):
            # Static assets - long cache with immutable
            patch_cache_control(response, max_age=31536000, immutable=True)  # 1 year
            response['CF-Cache-Status'] = 'HIT'
            
        elif self._is_marketplace_page(path):
            # Marketplace pages - medium cache
            patch_cache_control(response, max_age=1800, s_maxage=3600)  # 30min browser, 1hr edge
            response['Vary'] = 'Accept-Encoding'
            
        elif self._is_category_page(path):
            # Category pages - medium cache
            patch_cache_control(response, max_age=1800, s_maxage=3600)  # 30min browser, 1hr edge
            response['Vary'] = 'Accept-Encoding'
            
        else:
            # Default pages - short cache
            patch_cache_control(response, max_age=300, s_maxage=900)  # 5min browser, 15min edge
            response['Vary'] = 'Accept-Encoding'
        
        return response
    
    def _is_static_asset(self, path):
        """Check if the path is for a static asset"""
        static_extensions = ('.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2')
        return path.startswith('/static/') or any(path.endswith(ext) for ext in static_extensions)
    
    def _is_marketplace_page(self, path):
        """Check if the path is for the main marketplace page"""
        return path == '/' or path == '/marketplace/'
    
    def _is_category_page(self, path):
        """Check if the path is for a category page"""
        return path.startswith('/view/') and path.count('/') >= 2
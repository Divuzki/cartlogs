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
        
        # Don't cache for authenticated users OR pages with forms that need CSRF
        if request.user.is_authenticated or self._requires_csrf_protection(request.path):
            patch_cache_control(response, no_cache=True, no_store=True, must_revalidate=True)
            response['CF-Cache-Status'] = 'BYPASS'
            # Ensure CSRF cookie is set for pages that need it
            if self._requires_csrf_protection(request.path):
                response['Vary'] = 'Cookie'
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
    
    def _requires_csrf_protection(self, path):
        """Check if the path requires CSRF protection (has forms)"""
        csrf_protected_paths = [
            '/',  # Main marketplace page with checkout form
            '/marketplace/',  # Marketplace page
            '/auth/',  # Authentication pages
            '/checkout/',  # Checkout process
            '/add_funds/',  # Payment pages
            '/profile/',  # Profile pages
        ]
        
        # Check for exact matches or path prefixes
        for protected_path in csrf_protected_paths:
            if path == protected_path or path.startswith(protected_path):
                return True
        
        # Also check for view_all pages that contain checkout forms
        if path.startswith('/view/') and path.count('/') >= 2:
            return True
            
        return False
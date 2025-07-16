# Cloudflare & Redis Optimization Guide for CartLogs

## 🚀 Cloudflare Optimization for Maximum Speed

### 1. Page Rules Configuration

Set up these Page Rules in your Cloudflare dashboard (order matters):

#### Rule 1: Bypass Cache for Dynamic Pages
```
Pattern: yourdomain.com/orders*
Settings: Cache Level = Bypass
```

#### Rule 2: Bypass Cache for Authentication
```
Pattern: yourdomain.com/auth/*
Settings: Cache Level = Bypass
```

#### Rule 3: Bypass Cache for User-Specific Pages
```
Pattern: yourdomain.com/profile*
Settings: Cache Level = Bypass
```

#### Rule 4: Bypass Cache for Payment Pages
```
Pattern: yourdomain.com/checkout*
Settings: Cache Level = Bypass
```

#### Rule 5: Cache Static Assets
```
Pattern: yourdomain.com/static/*
Settings: 
- Cache Level = Cache Everything
- Edge Cache TTL = 1 month
- Browser Cache TTL = 1 month
```

#### Rule 6: Cache Public Pages
```
Pattern: yourdomain.com/marketplace*
Settings:
- Cache Level = Cache Everything
- Edge Cache TTL = 30 minutes
- Browser Cache TTL = 5 minutes
```

### 2. Cloudflare Settings Optimization

#### Speed Tab:
- ✅ Auto Minify: CSS, JavaScript, HTML
- ✅ Brotli Compression
- ✅ Early Hints
- ✅ HTTP/2 to Origin
- ✅ HTTP/3 (with QUIC)
- ✅ 0-RTT Connection Resumption

#### Caching Tab:
- Browser Cache TTL: 4 hours
- Always Online: ON
- Development Mode: OFF (for production)

#### Network Tab:
- HTTP/2: ON
- HTTP/3 (with QUIC): ON
- 0-RTT Connection Resumption: ON
- gRPC: ON
- WebSockets: ON
- Onion Routing: ON
- Pseudo IPv4: Add header

### 3. Cache Rules (New Cloudflare Feature)

If available, use Cache Rules instead of Page Rules:

#### Cache Rule 1: Static Assets
```
Expression: (http.request.uri.path matches "^/static/.*")
Action: Cache
Edge TTL: 30 days
Browser TTL: 7 days
```

#### Cache Rule 2: Public Marketplace
```
Expression: (http.request.uri.path matches "^/marketplace.*" and not http.request.uri.query contains "user")
Action: Cache
Edge TTL: 30 minutes
Browser TTL: 5 minutes
```

### 4. Transform Rules for Headers

Add these HTTP Response Header Modifications:

```
Rule Name: Security Headers
Expression: (true)
Headers:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: geolocation=(), microphone=(), camera=()
```

## 🔧 Cache Setup (Development vs Production)

### Development Environment

In development (DEBUG=True), the application uses **database caching** for simplicity:
- No Redis required
- Uses SQLite/PostgreSQL cache table
- Automatic fallback for all cache operations
- Run `python manage.py setup_cache` to create cache table

### Production Environment (Railway)

#### 1. Add Redis Service to Railway

1. Go to your Railway project dashboard
2. Click "+ New Service"
3. Select "Database" → "Redis"
4. Railway will automatically provision a Redis instance

#### 2. Environment Variables

Railway will automatically create a `REDIS_URL` environment variable:

```bash
# Required for production (automatically provided by Railway)
REDIS_URL=redis://default:password@host:port
DEBUG=False

# Optional: Custom Redis settings
REDIS_MAX_CONNECTIONS=20
REDIS_TIMEOUT=5
```

### 3. Railway Deployment Configuration

Create or update your `railway.toml`:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py warm_cache && gunicorn server.wsgi:application"
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3

[environments.production]
REDIS_URL = "${{Redis.REDIS_URL}}"
```

### 4. Testing Your Setup

#### Development Testing:
```bash
# Setup database cache
python manage.py setup_cache

# Test cache functionality
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'working')
>>> cache.get('test')  # Should return 'working'
```

#### Production Testing:
```bash
# Test Redis connection
railway run python manage.py setup_cache

# Check cache stats (staff only)
curl https://yourdomain.com/admin/cache/stats/
```

### 5. Cache Warming Strategy

Run these commands after deployment:

```bash
# Warm up the cache
railway run python manage.py warm_cache

# Set up a cron job (if using Railway Cron)
# Add this to your Railway project:
# Schedule: 0 */6 * * * (every 6 hours)
# Command: python manage.py warm_cache
```

## 📊 Performance Monitoring

### 1. Django Debug Toolbar (Development Only)

Add to your development settings:

```python
if DEBUG:
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    INTERNAL_IPS = ['127.0.0.1']
```

### 2. Cache Hit Rate Monitoring

Add this to your views for monitoring:

```python
from django.core.cache import cache
from django_redis import get_redis_connection

def cache_stats_view(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    redis_conn = get_redis_connection("default")
    info = redis_conn.info()
    
    return JsonResponse({
        'cache_hits': info.get('keyspace_hits', 0),
        'cache_misses': info.get('keyspace_misses', 0),
        'memory_usage': info.get('used_memory_human', 'N/A'),
        'connected_clients': info.get('connected_clients', 0),
    })
```

## 🔍 Cache Strategy Summary

### What We Cache:
- ✅ Marketplace listings (30 min - 1 hour)
- ✅ Category data (24 hours)
- ✅ Public account listings (30 minutes)
- ✅ Static content (30 days)
- ✅ User sessions (24 hours)

### What We DON'T Cache:
- ❌ User orders and order details
- ❌ Payment pages and checkout
- ❌ User authentication pages
- ❌ User profiles and wallets
- ❌ Admin pages
- ❌ API endpoints with user-specific data

## 🚨 Important Notes

1. **Cache Invalidation**: The system automatically clears relevant caches when data is updated
2. **User-Specific Data**: Never cache pages that show user-specific information
3. **CSRF Tokens**: Ensure CSRF tokens work correctly with cached pages
4. **Testing**: Always test caching in a staging environment first
5. **Monitoring**: Monitor cache hit rates and adjust timeouts as needed

## 🔧 Troubleshooting

### Redis Connection Issues:
```bash
# Test Redis connection
railway run python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value')
>>> cache.get('test')
```

### Clear All Cache:
```bash
railway run python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

### Check Cache Keys:
```bash
railway run python manage.py shell
>>> from django_redis import get_redis_connection
>>> redis_conn = get_redis_connection("default")
>>> redis_conn.keys("*")
```

This setup will significantly improve your application's performance by leveraging both Cloudflare's edge caching and Redis for application-level caching.
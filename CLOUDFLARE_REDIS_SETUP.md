# Cloudflare & Redis Optimization Guide for CartLogs

## 🆓 Free Tier Optimization Strategy

**Cloudflare Free Tier Limitations:**
- **3 Page Rules** maximum
- **10 Cache Rules** maximum
- **Limited expressions** - regex and advanced features require Business plan

### What You Can Actually Do:

#### ✅ Page Rules (3 available)
- Simple URL pattern matching with wildcards (`*`)
- Basic cache settings (Cache Everything, Bypass, etc.)
- TTL settings for edge and browser cache
- **No regex expressions** - only wildcard patterns

#### ✅ Cache Rules (10 available) 
- Basic field matching (URI, hostname, file extension)
- Simple operators (equals, contains, starts with, ends with)
- **Limited expressions** - no regex on free tier
- More granular than Page Rules but still restricted

#### ❌ Business Plan Required For:
- Regex expressions (`matches regex`)
- Advanced cache key customization
- Custom headers/cookies in expressions
- Complex logical operators

### Recommended Setup:
1. **Use both Page Rules AND Cache Rules** together
2. **Page Rules for broad patterns** (static assets, auth bypass)
3. **Cache Rules for specific targeting** (file extensions, exact paths)
4. **Keep expressions simple** - avoid regex and complex logic

---

## 🚀 Cloudflare Optimization for Maximum Speed

### 1. Page Rules Configuration (Free Tier - 3 Rules Max)

⚠️ **Cloudflare Free Tier Limitation**: You can only set 3 Page Rules. Here are the most impactful ones:

#### Rule 1: Cache Static Assets (Highest Priority)
```
Pattern: yourdomain.com/static/*
Settings: 
- Cache Level = Cache Everything
- Edge Cache TTL = 1 month
- Browser Cache TTL = 1 month
```
*This rule provides the biggest performance boost by caching CSS, JS, and images.*

#### Rule 2: Cache Public Marketplace (High Priority)
```
Pattern: yourdomain.com/marketplace*
Settings:
- Cache Level = Cache Everything
- Edge Cache TTL = 30 minutes
- Browser Cache TTL = 5 minutes
```
*Caches your main product pages for faster loading.*

#### Rule 3: Bypass Cache for User Areas (Essential)
```
Pattern: yourdomain.com/auth/*
Settings: Cache Level = Bypass
```
*Ensures authentication and user-specific pages work correctly.*

#### Additional Patterns to Consider:
If you need to modify these rules later, consider these patterns:
- `yourdomain.com/orders*` - Bypass cache for order pages
- `yourdomain.com/profile*` - Bypass cache for user profiles
- `yourdomain.com/checkout*` - Bypass cache for payment pages

💡 **Pro Tip**: Use Cache Rules (next section) for more granular control without Page Rule limitations.

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

### 3. Cache Rules (10 Available on Free Tier)

🎯 **Cache Rules complement Page Rules** - you get 10 Cache Rules vs only 3 Page Rules!

⚠️ **Free Tier Limitations**: <mcreference link="https://developers.cloudflare.com/cache/how-to/cache-rules/settings/" index="1">1</mcreference> <mcreference link="https://developers.cloudflare.com/cache/plans/" index="3">3</mcreference>
- **No regex expressions** - `matches regex` requires Business plan
- **Simple operators only** - equals, contains, starts with, ends with
- **Basic field matching** - URI, hostname, file extension

#### ✅ Cache Rule 1: Static Assets (Free Tier Compatible)
```
Field: File extension
Operator: is in
Value: css js png jpg jpeg gif svg ico woff woff2
Action: Cache
Edge TTL: 30 days
Browser TTL: 7 days
```

#### ✅ Cache Rule 2: CSS Files
```
Field: File extension
Operator: equals
Value: css
Action: Cache
Edge TTL: 30 days
Browser TTL: 7 days
```

#### ✅ Cache Rule 3: JavaScript Files
```
Field: File extension
Operator: equals
Value: js
Action: Cache
Edge TTL: 30 days
Browser TTL: 7 days
```

#### ✅ Cache Rule 4: Marketplace Pages
```
Field: URI Path
Operator: starts with
Value: /marketplace
Action: Cache
Edge TTL: 30 minutes
Browser TTL: 5 minutes
```

#### ✅ Cache Rule 5: Homepage
```
Field: URI Path
Operator: equals
Value: /
Action: Cache
Edge TTL: 1 hour
Browser TTL: 30 minutes
```

#### ❌ Examples That DON'T Work on Free Tier:
```
# These require Business plan:
Expression: (http.request.uri.path matches "^/static/.*")  # Regex
Expression: (http.request.uri.path matches "^/(auth|profile).*")  # Regex
Expression: (http.cookie contains "user_id")  # Advanced fields
```

💡 **Setup Instructions**:
1. Go to Cloudflare Dashboard → Caching → Cache Rules
2. Click "Create rule"
3. Use the **Expression Builder** (not "Edit expression")
4. Select fields and operators from dropdowns
5. Avoid typing custom expressions
6. Save and deploy

✅ **Advantages of Cache Rules**:
- 10 rules vs 3 Page Rules
- More specific targeting (file extensions)
- Better organization
- Easier to manage multiple rules

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

## 🚀 Quick Setup Checklist for Free Tier

### Step 1: Cache Rules (10 Available - Use Expression Builder)
- [ ] Cache Rule 1: File extension `is in` css,js,png,jpg,gif,svg,ico,woff
- [ ] Cache Rule 2: URI Path `starts with` /marketplace
- [ ] Cache Rule 3: URI Path `equals` / (homepage)
- [ ] Cache Rule 4: URI Path `starts with` /about
- [ ] Cache Rule 5: URI Path `starts with` /contact
- [ ] **Avoid**: Custom expressions or regex (requires Business plan)

### Step 2: Essential Page Rules (Only 3 Available)
- [ ] Rule 1: Cache Static Assets (`yourdomain.com/static/*`)
- [ ] Rule 2: Cache Marketplace (`yourdomain.com/marketplace*`)
- [ ] Rule 3: Bypass Auth (`yourdomain.com/auth/*`)

### ⚠️ Important Notes:
- **Both rule types work together** - you can use all 3 Page Rules + 10 Cache Rules
- **Page Rules use wildcards** (`*`) - no regex needed
- **Cache Rules use dropdowns** - select fields/operators, don't type expressions
- **Test each rule** after creation to ensure it works

### Step 3: Cloudflare Settings
- [ ] Enable Auto Minify (CSS, JS, HTML)
- [ ] Enable Brotli Compression
- [ ] Enable HTTP/2 and HTTP/3
- [ ] Set Browser Cache TTL to 4 hours
- [ ] Add Security Headers via Transform Rules

### Step 4: Redis Setup (Production)
- [ ] Add Redis service to Railway
- [ ] Set `DEBUG=False` and `REDIS_URL` environment variables
- [ ] Run `python manage.py setup_cache`
- [ ] Run `python manage.py warm_cache`

### Step 5: Monitor Performance
- [ ] Check cache stats at `/admin/cache/stats/`
- [ ] Monitor cache hit rates
- [ ] Test page load speeds

---

This setup will significantly improve your application's performance by leveraging both Cloudflare's edge caching and Redis for application-level caching, optimized specifically for the free tier limitations.
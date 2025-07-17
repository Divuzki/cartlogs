# Cloudflare CSRF Token Fix

## Problem Description

Some users were experiencing "403 Forbidden - CSRF verification failed" errors during checkout, while others could complete the process successfully. This inconsistent behavior indicated a caching issue rather than a code problem.

## Root Cause Analysis

The issue was caused by Cloudflare's cache configuration that was:

1. **Ignoring CSRF cookies in cache keys**: The cache rule was set to ignore cookies including `csrftoken`
2. **Caching pages with forms**: Pages containing checkout forms were being cached and served to different users
3. **Serving stale CSRF tokens**: Users received cached pages with CSRF tokens that didn't match their session

## Solution Implementation

### 1. Enhanced CSRF Cookie Settings

**File**: `/server/settings.py`

```python
# CSRF Cookie Settings - Critical for Cloudflare compatibility
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_HTTPONLY = False  # Must be False so JavaScript can access it
CSRF_COOKIE_SAMESITE = 'Lax'  # CSRF protection
CSRF_USE_SESSIONS = False  # Use cookies instead of sessions for CSRF tokens
CSRF_COOKIE_AGE = 31449600  # 1 year - longer than session to prevent issues
```

**Key Changes**:
- `CSRF_COOKIE_HTTPONLY = False`: Allows JavaScript to access CSRF tokens
- `CSRF_USE_SESSIONS = False`: Uses cookies instead of sessions for better Cloudflare compatibility
- `CSRF_COOKIE_AGE = 31449600`: Sets longer expiration to prevent token expiry issues

### 2. Updated CloudflareCacheMiddleware

**File**: `/server/middleware.py`

**Enhanced Logic**:
- Bypasses cache for pages requiring CSRF protection
- Identifies form-containing pages automatically
- Sets appropriate cache headers for different page types

**Protected Paths**:
- `/` (Main marketplace with checkout form)
- `/marketplace/` (Marketplace page)
- `/auth/` (Authentication pages)
- `/checkout/` (Checkout process)
- `/add_funds/` (Payment pages)
- `/profile/` (Profile pages)
- `/view/*` (Category pages with checkout forms)

## Required Cloudflare Configuration Changes (Pro Plan)

### 1. Page Rules (Pro Plan Feature)

**Critical: Create Page Rules for Form Pages**

**Rule 1: Bypass Cache for Main Pages with Forms**
```
URL Pattern: cartlogs.com/
Settings:
- Cache Level: Bypass
- Security Level: Medium
```

**Rule 2: Bypass Cache for Category Pages**
```
URL Pattern: cartlogs.com/view/*
Settings:
- Cache Level: Bypass
- Security Level: Medium
```

**Rule 3: Bypass Cache for Auth Pages**
```
URL Pattern: cartlogs.com/auth/*
Settings:
- Cache Level: Bypass
- Security Level: High
```

**Rule 4: Bypass Cache for Checkout**
```
URL Pattern: cartlogs.com/checkout*
Settings:
- Cache Level: Bypass
- Security Level: High
- Browser Integrity Check: On
```

### 2. Caching Configuration (Pro Plan)

**Note**: Pro Plan doesn't have Cache Rules (Business+ feature). Use Page Rules instead.

**Keep Existing Cache Settings for Static Assets**:
- CSS, JS, Images will still be cached automatically
- No additional configuration needed for static content

### 3. Static Assets Caching (Automatic)

**Pro Plan Automatic Caching**:
- Static files (CSS, JS, images) are cached automatically
- No additional Page Rules needed for static content
- Cloudflare automatically detects and caches static assets
- Default cache TTL applies (respects origin headers)

## Testing Checklist

- [ ] Anonymous users can browse marketplace without CSRF errors
- [ ] Authenticated users can complete checkout process
- [ ] CSRF tokens are fresh on each page load for form pages
- [ ] Static assets are still properly cached
- [ ] No cross-user data leakage
- [ ] Performance is maintained for cacheable content

## Monitoring

### Key Metrics to Watch

1. **CSRF Error Rate**: Should drop to near zero
2. **Cache Hit Ratio**: May decrease slightly for form pages (expected)
3. **Checkout Completion Rate**: Should improve
4. **Page Load Times**: Should remain consistent

### Cloudflare Analytics

- Monitor cache hit ratios in Cloudflare Analytics
- Check for any increase in origin requests
- Verify that static assets maintain high cache hit ratios

## Pro Plan Limitations

**Features NOT Available on Pro Plan**:
- ❌ Cache Rules (Business+ only)
- ❌ Advanced Rate Limiting (Business+ only)
- ❌ Bot Management (Enterprise only)
- ❌ Custom WAF Rules (Business+ only)
- ❌ Load Balancing (Business+ only)

**Available Pro Plan Solutions**:
- ✅ Page Rules (up to 20 rules)
- ✅ Basic security settings
- ✅ Auto minification
- ✅ Basic analytics
- ✅ SSL/TLS settings

## Implementation Priority (Pro Plan)

1. **Immediate**: Create Page Rules to bypass cache for form pages
2. **Deploy**: Django middleware changes (already implemented)
3. **Configure**: Enable Pro Plan security and performance features
4. **Monitor**: Watch Cloudflare Analytics for 24-48 hours
5. **Optimize**: Adjust Page Rules based on traffic patterns

## Rollback Plan

If issues arise:

1. **Cloudflare**: Revert cache rule changes
2. **Django**: Remove CSRF cookie settings additions
3. **Middleware**: Revert to previous caching logic

## Additional Pro Plan Recommendations

### 1. Security Settings

**Enable Available Pro Plan Security Features**:
- **Security Level**: Set to "Medium" for most pages, "High" for sensitive areas
- **Challenge Passage**: 30 minutes (helps with legitimate users)
- **Browser Integrity Check**: Enable for checkout and auth pages
- **Always Use HTTPS**: Enable to force SSL

### 2. Performance Optimization

**Pro Plan Performance Features**:
- **Auto Minify**: Enable for HTML, CSS, and JavaScript
- **Brotli Compression**: Enable for better compression
- **HTTP/2**: Enable (should be on by default)
- **0-RTT Connection Resumption**: Enable for faster connections

### 3. Monitoring (Pro Plan)

**Available Analytics**:
- Monitor cache hit ratios in Cloudflare Analytics
- Track security events and challenges
- Watch for any unusual traffic patterns
- Use Web Analytics (free tier) for basic insights

**Note**: Advanced features like Bot Management, Rate Limiting, and detailed WAF rules require Business+ plans.

This fix ensures that CSRF tokens are properly handled while maintaining Cloudflare's performance benefits for appropriate content.
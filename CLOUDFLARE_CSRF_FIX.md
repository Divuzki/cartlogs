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

## Required Cloudflare Configuration Changes

### 1. Update Cache Rules

**Current Problematic Rule**:
```
Expression: (http.request.full_uri eq "cartlogs.com/") or (http.request.full_uri wildcard "*cartlogs.com/view_all/*")
Custom Cache Key: Ignore cookies (sessionid, csrftoken, _ga, _gid)
```

**Recommended Fix**:
```
Expression: (http.request.full_uri eq "cartlogs.com/") or (http.request.full_uri wildcard "*cartlogs.com/view_all/*")
Custom Cache Key: Ignore cookies (_ga, _gid) BUT INCLUDE (sessionid, csrftoken)
```

### 2. Create Specific Rules for Form Pages

**New Rule for Pages with Forms**:
```
Rule Name: Bypass Cache for Form Pages
Expression: (http.request.uri.path in {"/" "/marketplace/" "/checkout/"}) or (http.request.uri.path wildcard "/view/*") or (http.request.uri.path wildcard "/auth/*")
Action: Bypass Cache
Reason: These pages contain forms that require fresh CSRF tokens
```

### 3. Static Assets Caching (Keep Existing)

```
Rule Name: Cache Static Assets
Expression: (http.request.uri.path.extension in {"css" "js" "png" "jpg" "jpeg" "gif" "svg" "ico" "woff" "woff2"})
Action: Cache Everything
Edge Cache TTL: 1 month
Browser Cache TTL: 1 month
Ignore Query String: On
```

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

## Implementation Priority

1. **Immediate**: Update Cloudflare cache rules (fixes the issue instantly)
2. **Deploy**: Django code changes (provides additional protection)
3. **Monitor**: Watch metrics for 24-48 hours
4. **Optimize**: Fine-tune cache rules based on analytics

## Rollback Plan

If issues arise:

1. **Cloudflare**: Revert cache rule changes
2. **Django**: Remove CSRF cookie settings additions
3. **Middleware**: Revert to previous caching logic

## Additional Recommendations

### 1. Consider Page Rules for Critical Paths

```
URL Pattern: cartlogs.com/checkout*
Settings: 
- Cache Level: Bypass
- Security Level: High
- Browser Integrity Check: On
```

### 2. Enable Bot Fight Mode

To prevent automated attacks on checkout endpoints:
- Enable Bot Fight Mode in Cloudflare Security settings
- Configure rate limiting for checkout endpoints

### 3. Monitor Core Web Vitals

Ensure the fix doesn't impact performance:
- Track Largest Contentful Paint (LCP)
- Monitor First Input Delay (FID)
- Watch Cumulative Layout Shift (CLS)

This fix ensures that CSRF tokens are properly handled while maintaining Cloudflare's performance benefits for appropriate content.
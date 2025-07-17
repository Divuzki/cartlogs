#!/usr/bin/env python
"""
CSRF Token Fix Verification Script

This script tests the CSRF token handling to ensure the Cloudflare fix is working correctly.
"""

import requests
import re
from urllib.parse import urljoin

def test_csrf_token_consistency(base_url="http://127.0.0.1:8000"):
    """
    Test that CSRF tokens are consistent and properly handled
    """
    session = requests.Session()
    
    print("🔍 Testing CSRF Token Handling...")
    print(f"Base URL: {base_url}")
    print("-" * 50)
    
    # Test 1: Get marketplace page and extract CSRF token
    print("1. Testing marketplace page CSRF token...")
    response = session.get(base_url)
    
    if response.status_code == 200:
        # Extract CSRF token from HTML
        csrf_match = re.search(r'name=["\']csrfmiddlewaretoken["\']\s+value=["\']([^"\'>]+)["\']', response.text)
        if csrf_match:
            csrf_token_html = csrf_match.group(1)
            print(f"   ✅ CSRF token found in HTML: {csrf_token_html[:20]}...")
        else:
            print("   ❌ No CSRF token found in HTML")
            return False
        
        # Check CSRF cookie
        csrf_cookie = session.cookies.get('csrftoken')
        if csrf_cookie:
            print(f"   ✅ CSRF cookie set: {csrf_cookie[:20]}...")
        else:
            print("   ❌ No CSRF cookie found")
            return False
        
        # Verify they match
        if csrf_token_html == csrf_cookie:
            print("   ✅ HTML token matches cookie")
        else:
            print("   ⚠️  HTML token differs from cookie (this might be expected)")
    else:
        print(f"   ❌ Failed to load marketplace page: {response.status_code}")
        return False
    
    # Test 2: Check cache headers
    print("\n2. Testing cache headers...")
    cache_control = response.headers.get('Cache-Control', '')
    cf_cache_status = response.headers.get('CF-Cache-Status', 'Not set')
    
    print(f"   Cache-Control: {cache_control}")
    print(f"   CF-Cache-Status: {cf_cache_status}")
    
    if 'no-cache' in cache_control or cf_cache_status == 'BYPASS':
        print("   ✅ Page is properly bypassing cache")
    else:
        print("   ⚠️  Page might be cached (check Cloudflare settings)")
    
    # Test 3: Test multiple requests for token consistency
    print("\n3. Testing token consistency across requests...")
    tokens = []
    for i in range(3):
        resp = session.get(base_url)
        if resp.status_code == 200:
            token_match = re.search(r'name=["\']csrfmiddlewaretoken["\']\s+value=["\']([^"\'>]+)["\']', resp.text)
            if token_match:
                tokens.append(token_match.group(1))
    
    if len(set(tokens)) == 1:
        print(f"   ✅ CSRF tokens are consistent across requests: {tokens[0][:20]}...")
    else:
        print(f"   ⚠️  CSRF tokens vary across requests: {len(set(tokens))} unique tokens")
        print("      This might indicate caching issues")
    
    # Test 4: Test different pages
    print("\n4. Testing different page types...")
    test_pages = [
        ('/', 'Homepage'),
        ('/auth/', 'Auth page'),
    ]
    
    for path, name in test_pages:
        url = urljoin(base_url, path)
        resp = session.get(url)
        cache_control = resp.headers.get('Cache-Control', '')
        cf_cache_status = resp.headers.get('CF-Cache-Status', 'Not set')
        
        print(f"   {name} ({path}):")
        print(f"     Status: {resp.status_code}")
        print(f"     Cache-Control: {cache_control}")
        print(f"     CF-Cache-Status: {cf_cache_status}")
        
        if resp.status_code == 200 and ('no-cache' in cache_control or cf_cache_status == 'BYPASS'):
            print(f"     ✅ Properly bypassing cache")
        elif resp.status_code == 404:
            print(f"     ⚠️  Page not found (expected for some paths)")
        else:
            print(f"     ⚠️  Check cache configuration")
    
    print("\n" + "="*50)
    print("🎯 CSRF Fix Verification Complete")
    print("\n📋 Next Steps:")
    print("1. Update Cloudflare cache rules as documented in CLOUDFLARE_CSRF_FIX.md")
    print("2. Monitor checkout success rates")
    print("3. Check Cloudflare Analytics for cache hit ratio changes")
    print("\n⚠️  Note: Full fix requires Cloudflare configuration changes!")
    
    return True

if __name__ == "__main__":
    test_csrf_token_consistency()
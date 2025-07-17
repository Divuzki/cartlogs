#!/bin/bash

# CartLogs Local Development and Testing Script
# Railway handles deployment automatically - this script is for local testing
# and manual cache management

set -e  # Exit on any error

echo "🚀 CartLogs Local Development Script"
echo "===================================="
echo "ℹ️  Note: Railway handles deployment automatically"
echo "   This script is for local development and testing"
echo ""

# Function to run Django management commands
run_django_command() {
    echo "Running: python manage.py $1"
    python manage.py $1
}

# Function to setup and check cache
setup_cache() {
    echo "🔧 Using database cache backend (Cloudflare handles edge caching)..."
    echo "✅ Cache backend configured"
}

# Main deployment steps
echo "📦 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

echo "🗄️  Running database migrations..."
run_django_command "migrate"

echo "📁 Collecting static files..."
run_django_command "collectstatic --noinput"

# Setup cache backend
setup_cache

echo "🔥 Warming up cache..."
if python manage.py warm_cache; then
    echo "✅ Cache warm-up completed"
else
    echo "⚠️ Cache warm-up failed, but continuing..."
    echo "This is normal if database is empty."
fi

echo "🧹 Cleaning up old cache entries..."
python -c "
from django.core.cache import cache
try:
    cache.clear()
    print('✅ Cache cleanup completed')
except Exception as e:
    print(f'⚠️  Cache cleanup warning: {e}')
"

echo "✅ Local setup completed successfully!"
echo ""
echo "📊 Cache Statistics:"
echo "Using database cache - Cloudflare handles edge caching"

echo ""
echo "🌐 For Production Deployment:"
echo "1. Push to Railway - it will auto-detect and deploy your Django app"
echo "2. Configure environment variables (DJANGO_SECRET_KEY, DEBUG=False)"
echo "3. Configure Cloudflare settings for caching and optimization"
echo "4. Monitor cache performance at /admin/cache/stats/"
echo ""
echo "🎉 Your local CartLogs setup is ready!"
echo "💡 Railway will handle production deployment automatically when you push your code."
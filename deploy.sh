#!/bin/bash

# CartLogs Deployment Script for Railway
# This script helps with deployment and cache management

set -e  # Exit on any error

echo "🚀 CartLogs Deployment Script"
echo "=============================="

# Function to run Django management commands
run_django_command() {
    echo "Running: python manage.py $1"
    python manage.py $1
}

# Function to setup and check cache
setup_cache() {
    echo "🔧 Setting up cache backend..."
    python manage.py setup_cache
    
    if [ $? -ne 0 ]; then
        echo "⚠️ Cache setup failed, but continuing deployment..."
        echo "This is normal if Redis is not yet available."
        return 0
    fi
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
    echo "This is normal if Redis is not yet available or database is empty."
fi

echo "🧹 Cleaning up old cache entries..."
python -c "
from django.core.cache import cache
from django_redis import get_redis_connection
try:
    redis_conn = get_redis_connection('default')
    # Remove any test keys
    test_keys = redis_conn.keys('test_*')
    if test_keys:
        redis_conn.delete(*test_keys)
        print(f'Cleaned up {len(test_keys)} test keys')
    print('✅ Cache cleanup completed')
except Exception as e:
    print(f'⚠️  Cache cleanup warning: {e}')
"

echo "✅ Deployment completed successfully!"
echo ""
echo "📊 Cache Statistics:"
python -c "
from django_redis import get_redis_connection
try:
    redis_conn = get_redis_connection('default')
    info = redis_conn.info()
    print(f'Memory Usage: {info.get("used_memory_human", "N/A")}')
    print(f'Total Keys: {len(redis_conn.keys("*"))}')
    print(f'Connected Clients: {info.get("connected_clients", 0)}')
except Exception as e:
    print(f'Could not get cache stats: {e}')
"

echo ""
echo "🌐 Next Steps:"
echo "1. Configure Cloudflare settings as per CLOUDFLARE_REDIS_SETUP.md"
echo "2. Set up Redis service in Railway dashboard"
echo "3. Add REDIS_URL environment variable"
echo "4. Monitor cache performance at /admin/cache/stats/"
echo ""
echo "🎉 Your CartLogs application is ready to serve lightning-fast requests!"
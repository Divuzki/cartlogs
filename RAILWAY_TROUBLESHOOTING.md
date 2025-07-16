# Railway Deployment Troubleshooting Guide

## 🚨 500 Error Diagnosis

### Step 1: Check Railway Logs
```bash
# Install Railway CLI if not already installed
npm install -g @railway/cli

# Login to Railway
railway login

# View deployment logs
railway logs

# View specific service logs
railway logs --service=your-service-name
```

### Step 2: Verify Environment Variables
Ensure these environment variables are set in Railway:

**Required:**
- `DJANGO_SECRET_KEY` - Your Django secret key
- `DEBUG=False` - Must be False for production
- `DATABASE_URL` - Automatically provided by Railway PostgreSQL

**Optional but Recommended:**
- `REDIS_URL` - Automatically provided by Railway Redis
- `USE_S3=False` - Set to True if using AWS S3
- `KORAPAY_SECRET_KEY` - For payment processing
- `KORAPAY_PUBLIC_KEY` - For payment processing

### Step 3: Common Issues and Solutions

#### Issue 1: Missing SECRET_KEY
**Error:** `django.core.exceptions.ImproperlyConfigured: The SECRET_KEY setting must not be empty`
**Solution:** Set `DJANGO_SECRET_KEY` environment variable in Railway

#### Issue 2: Database Connection
**Error:** Database connection errors
**Solution:** 
1. Ensure PostgreSQL service is added to your Railway project
2. Check that `DATABASE_URL` is automatically set
3. Run migrations: `railway run python manage.py migrate`

#### Issue 3: Static Files
**Error:** Static files not loading
**Solution:**
1. Ensure `collectstatic` runs during deployment (check Procfile)
2. Verify WhiteNoise is properly configured

#### Issue 4: Cache Setup Failure
**Error:** Redis connection errors
**Solution:**
1. Add Redis service in Railway dashboard
2. Verify `REDIS_URL` environment variable is set
3. Cache setup is now optional and won't block deployment

#### Issue 5: warm_cache Command Failure
**Error:** `python manage.py warm_cache` fails in production
**Common Causes:**
- Empty database (no SocialMediaAccount or Category records)
- Redis not available or misconfigured
- Database connection issues
- Missing environment variables

**Solution:**
1. **Check if database has data:**
   ```bash
   railway shell
   python manage.py shell
   >>> from marketplace.models import SocialMediaAccount, Category
   >>> print(f"Accounts: {SocialMediaAccount.objects.count()}")
   >>> print(f"Categories: {Category.objects.count()}")
   ```

2. **Test cache connection:**
   ```bash
   python manage.py setup_cache
   ```

3. **Run warm_cache with verbose output:**
   ```bash
   python manage.py warm_cache --verbosity=2
   ```

4. **If database is empty, populate it first:**
   - Add categories and social media accounts through Django admin
   - Or load fixtures if available

**Note:** The warm_cache command now has improved error handling and will complete gracefully even if some operations fail.

### Step 4: Manual Deployment Commands
If automatic deployment fails, try running commands manually:

```bash
# Connect to Railway shell
railway shell

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Test cache setup (optional)
python manage.py setup_cache

# Create superuser (if needed)
python manage.py createsuperuser
```

### Step 5: Test Local Production Settings
```bash
# Set environment variables locally
export DEBUG=False
export DJANGO_SECRET_KEY="your-secret-key-here"
export DATABASE_URL="your-database-url"

# Test with production settings
python manage.py runserver
```

### Step 6: Check Application Health
Once deployed, test these endpoints:
- `/` - Homepage
- `/admin/` - Admin panel
- `/marketplace/` - Marketplace
- `/auth/` - Authentication

## 🔧 Quick Fixes Applied

1. **Added Procfile** - Railway now knows how to start the application
2. **Added railway.toml** - Proper deployment configuration
3. **Made cache setup optional** - Won't block deployment if Redis isn't ready
4. **Updated ALLOWED_HOSTS** - Includes Railway domains
5. **Improved error handling** - Deployment continues even if cache fails

## 📞 Getting Help

If the issue persists:
1. Check Railway logs for specific error messages
2. Verify all environment variables are set correctly
3. Ensure PostgreSQL and Redis services are running
4. Test the application locally with production settings

## 🚀 Next Steps After Fixing

1. Set up Redis service for caching
2. Configure custom domain
3. Set up monitoring and logging
4. Configure Cloudflare as per CLOUDFLARE_REDIS_SETUP.md
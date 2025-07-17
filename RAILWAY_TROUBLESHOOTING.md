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
- `USE_S3=False` - Set to True if using AWS S3
- `KORAPAY_SECRET_KEY` - For payment processing
- `KORAPAY_PUBLIC_KEY` - For payment processing

### Step 3: Common Issues and Solutions

#### Issue 1: Database Connection During Build
**Error:** `django.db.utils.OperationalError: could not translate host name "postgres.railway.internal" to address: Name or service not known`

**Root Cause:** Database operations are trying to run before the database service is available.

**Solution:** Railway's auto-detection handles this automatically by:
- Running migrations after the database is available
- Collecting static files at the appropriate time
- Starting the web server with proper timing

If issues persist, ensure your PostgreSQL service is properly connected to your project.

#### Issue 2: Missing SECRET_KEY
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
1. Railway automatically runs `collectstatic` during deployment
2. Verify WhiteNoise is properly configured in settings.py
3. Check that `STATIC_URL` and `STATIC_ROOT` are correctly set

#### Issue 4: Cache Setup
**Note:** Application now uses database cache with Cloudflare handling edge caching
**Solution:**
1. No additional cache service setup required
2. Cloudflare provides edge caching for performance

#### Issue 5: warm_cache Command Failure
**Error:** `python manage.py warm_cache` fails in production
**Common Causes:**
- Empty database (no SocialMediaAccount or Category records)
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

2. **Cache is now database-based:**
   - No additional setup required
   - Cloudflare handles edge caching

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

# Cache is now database-based (no setup needed)

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

1. **Railway Auto-Detection** - Railway automatically detects Django applications and handles deployment
2. **Simplified cache setup** - Using database cache with Cloudflare edge caching
3. **Updated ALLOWED_HOSTS** - Includes Railway domains
4. **Improved error handling** - Deployment continues even if cache fails
5. **Enhanced warm_cache command** - Better error handling and graceful failures

## 📞 Getting Help

If the issue persists:
1. Check Railway logs for specific error messages
2. Verify all environment variables are set correctly
3. Ensure PostgreSQL service is running
4. Test the application locally with production settings

## 🚀 Next Steps After Fixing

1. Configure custom domain
2. Set up monitoring and logging
3. Configure Cloudflare for caching and optimization
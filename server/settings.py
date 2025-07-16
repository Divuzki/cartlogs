import os
from pathlib import Path
import dj_database_url

# dotenv
from dotenv import load_dotenv
load_dotenv(".env")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", 'django-insecure-=m%lj8zxnc)-*z7umq$(e*a@(1zemldxaz!c^gg304(!w*wkzo')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"
USE_S3 = os.getenv("USE_S3", "False") == "True"

ALLOWED_HOSTS = ["*"]

LOGIN_URL = "/auth/"

PAYMENT_GATEWAYS = {
    'korapay': {
        'name': 'Korapay',
        'min_amount': 1000,  # 100 Naira minimum
        'max_amount': 10000000,  # 10 million Naira maximum
    },
    # 'manual': {
    #     'name': 'Manual Bank Transfer',
    #     'min_amount': 1000,  # 100 Naira minimum
    #     'max_amount': 10000000,  # 10 million Naira maximum
    # }
}

KORAPAY_SECRET_KEY = os.environ.get('KORAPAY_SECRET_KEY')
KORAPAY_PUBLIC_KEY = os.environ.get('KORAPAY_PUBLIC_KEY')

CSRF_COOKIE_SECURE = DEBUG == False
SESSION_COOKIE_SECURE = DEBUG == False
SECURE_SSL_REDIRECT = DEBUG == False
SECURE_HSTS_SECONDS = 518400 if (DEBUG == False) else None
SECURE_HSTS_INCLUDE_SUBDOMAINS = DEBUG == False
SECURE_HSTS_PRELOAD = DEBUG == False
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https") if (DEBUG == False) else None
)

# CSRF and CORS Settings
CSRF_TRUSTED_ORIGINS = [
    "https://www.cartlogs.com",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

CORS_ALLOWED_ORIGINS = CSRF_TRUSTED_ORIGINS
CORS_ALLOW_CREDENTIALS = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'marketplace',
    'core'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'server.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates'
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'server.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

db_from_env = dj_database_url.config(conn_max_age=600)
DATABASES["default"].update(db_from_env)

# Cache Configuration - Only use Redis in production
if not DEBUG and os.environ.get('REDIS_URL'):
    # Redis Cache Configuration for Production
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 20,
                    'retry_on_timeout': True,
                },
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            },
            'KEY_PREFIX': 'cartlogs',
            'TIMEOUT': 300,  # 5 minutes default
        }
    }
    
    # Use Redis for sessions in production
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    # Use database cache for development
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'cache_table',
        }
    }
    
    # Use database sessions in development
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Session settings
SESSION_COOKIE_AGE = 86400  # 24 hours

# Cache timeout settings
CACHE_TIMEOUT_SHORT = 300      # 5 minutes - for frequently changing data
CACHE_TIMEOUT_MEDIUM = 1800    # 30 minutes - for moderately changing data
CACHE_TIMEOUT_LONG = 3600      # 1 hour - for rarely changing data
CACHE_TIMEOUT_VERY_LONG = 86400  # 24 hours - for static-like data


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

if USE_S3:
    # aws settings
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_DEFAULT_ACL = os.getenv("AWS_DEFAULT_ACL")
    AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3.us-east-1.amazonaws.com"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    AWS_S3_SECURE_URLS = True

    # s3 static settings
    STATIC_LOCATION = "static"
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/"
    STATICFILES_STORAGE = "server.storage_backends.StaticStorage"
    COMPRESS_URL = STATIC_URL
    COMPRESS_ROOT = BASE_DIR / "/static-root/"
    COMPRESS_STORAGE = "server.storage_backends.CachedStaticS3BotoStorage"

    # s3 public media settings
    PUBLIC_MEDIA_LOCATION = "media"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/"
    DEFAULT_FILE_STORAGE = "server.storage_backends.PublicMediaStorage"
    # STATIC_ROOT = BASE_DIR / "static-root"


elif not USE_S3:
    STATIC_URL = "/static/"
    MEDIA_URL = "/media/"
    STATIC_ROOT = BASE_DIR / "static-root"
    MEDIA_ROOT = BASE_DIR / "media-root"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# EMAIL_INFOS
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
DEFAULT_FROM_EMAIL = "CartLogs <{}>".format(EMAIL_HOST_USER)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", EMAIL_HOST_USER)
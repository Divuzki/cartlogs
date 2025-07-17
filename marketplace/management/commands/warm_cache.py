from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
from marketplace.models import SocialMediaAccount, Category
from core.cache_utils import cache_queryset
from django.db import connection


class Command(BaseCommand):
    help = 'Warm up the cache with frequently accessed data (Cloudflare-optimized)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force-anonymous',
            action='store_true',
            help='Force caching of anonymous user data (not recommended with Cloudflare)',
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write('Starting cache warm-up...')
            
            # Test database connection first
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            
            # Test cache connection
            cache.set('warm_cache_test', 'working', 10)
            if cache.get('warm_cache_test') != 'working':
                self.stdout.write(
                    self.style.WARNING('⚠️ Cache not working, skipping warm-up')
                )
                return
            cache.delete('warm_cache_test')
            
            # Warm up marketplace accounts cache (only if forced or for authenticated users)
            force_anonymous = options.get('force_anonymous', False)
            if force_anonymous:
                try:
                    self.stdout.write('Caching marketplace accounts (forced)...')
                    accounts_queryset = SocialMediaAccount.objects.filter(is_active=True)
                    cache_queryset(accounts_queryset, 'marketplace_accounts_all', timeout=settings.CACHE_TIMEOUT_LONG, force_cache=True)
                    self.stdout.write('✅ Marketplace accounts cached')
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Failed to cache marketplace accounts: {e}')
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS('⚡ Skipping anonymous user cache warming - Cloudflare handles this')
                )
            
            # Warm up category-specific caches (only if forced)
            if force_anonymous:
                try:
                    categories = Category.objects.all()
                    for category in categories:
                        try:
                            self.stdout.write(f'Caching accounts for {category.slug} (forced)...')
                            category_accounts = SocialMediaAccount.objects.filter(
                                is_active=True, 
                                category__slug=category.slug
                            )
                            cache_key = f'accounts_{category.slug}'
                            cache_queryset(category_accounts, cache_key, timeout=settings.CACHE_TIMEOUT_MEDIUM, force_cache=True)
                        except Exception as e:
                            self.stdout.write(
                                self.style.WARNING(f'⚠️ Failed to cache category {category.slug}: {e}')
                            )
                            continue
                    self.stdout.write('✅ Category-specific caches completed')
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ Failed to process categories: {e}')
                    )
            else:
                self.stdout.write(
                    self.style.SUCCESS('⚡ Skipping category cache warming - Cloudflare handles this')
                )
            
            # Cache categories (administrative data - still useful locally)
            try:
                self.stdout.write('Caching categories (admin data)...')
                categories_queryset = Category.objects.all()
                cache_queryset(categories_queryset, 'all_categories', timeout=settings.CACHE_TIMEOUT_VERY_LONG, force_cache=True)
                self.stdout.write('✅ Categories cached')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ Failed to cache categories: {e}')
                )
            
            self.stdout.write(
                self.style.SUCCESS('🚀 Cloudflare-optimized cache warm-up completed!')
            )
            self.stdout.write(
                self.style.SUCCESS('💡 Anonymous user data is cached by Cloudflare at the edge')
            )
            if not force_anonymous:
                self.stdout.write(
                    self.style.SUCCESS('   Use --force-anonymous to cache anonymous data locally')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Cache warm-up failed: {e}')
            )
            self.stdout.write(
                self.style.WARNING('This is normal if database is empty or cache is not available')
            )
            # Don't raise the exception - let the command complete gracefully
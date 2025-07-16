from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
from marketplace.models import SocialMediaAccount, Category
from core.cache_utils import cache_queryset


class Command(BaseCommand):
    help = 'Warm up the cache with frequently accessed data'

    def handle(self, *args, **options):
        self.stdout.write('Starting cache warm-up...')
        
        # Warm up marketplace accounts cache
        self.stdout.write('Caching marketplace accounts...')
        accounts_queryset = SocialMediaAccount.objects.filter(is_active=True)
        cache_queryset(accounts_queryset, 'marketplace_accounts_all', timeout=settings.CACHE_TIMEOUT_LONG)
        
        # Warm up category-specific caches
        categories = Category.objects.all()
        for category in categories:
            self.stdout.write(f'Caching accounts for {category.slug}...')
            category_accounts = SocialMediaAccount.objects.filter(
                is_active=True, 
                category__slug=category.slug
            )
            cache_key = f'accounts_{category.slug}'
            cache_queryset(category_accounts, cache_key, timeout=settings.CACHE_TIMEOUT_MEDIUM)
        
        # Cache categories
        self.stdout.write('Caching categories...')
        categories_queryset = Category.objects.all()
        cache_queryset(categories_queryset, 'all_categories', timeout=settings.CACHE_TIMEOUT_VERY_LONG)
        
        self.stdout.write(
            self.style.SUCCESS('Cache warm-up completed successfully!')
        )
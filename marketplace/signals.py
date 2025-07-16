from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import SocialMediaAccount, Category
from core.cache_utils import invalidate_cache_pattern


@receiver([post_save, post_delete], sender=SocialMediaAccount)
def invalidate_account_cache(sender, instance, **kwargs):
    """Invalidate cache when SocialMediaAccount is modified"""
    # Clear specific account caches
    cache_keys_to_clear = [
        f'accounts_{instance.category.slug}',
        'marketplace_accounts_all',
    ]
    
    for key in cache_keys_to_clear:
        cache.delete(key)
    
    # Clear view caches
    invalidate_cache_pattern('view_all')
    invalidate_cache_pattern('marketplace')


@receiver([post_save, post_delete], sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    """Invalidate cache when Category is modified"""
    # Clear all marketplace related caches
    invalidate_cache_pattern('marketplace')
    invalidate_cache_pattern('view_all')
    cache.delete('marketplace_accounts_all')
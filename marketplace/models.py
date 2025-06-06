from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from core.models import Transaction


class Log(models.Model):
    order_item = models.ForeignKey("marketplace.OrderItem", on_delete=models.CASCADE, related_name='logs', null=True, blank=True, editable=False)
    account = models.ForeignKey("marketplace.SocialMediaAccount", on_delete=models.CASCADE)
    log_data = models.TextField()
    is_active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for {self.account}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, null=True)
    position = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['position', 'created_at']
    
    def __str__(self):
        return self.name
    
    # automatically create slug from name
    def save(self, *args, **kwargs):
        self.slug = self.name.lower().replace(' ', '-')
        
        # Handle position assignment with date-based conflict resolution
        if not self.pk:  # New category
            if self.position == 0:
                # Get the highest position and add 1
                max_position = Category.objects.aggregate(max_pos=models.Max('position'))['max_pos']
                self.position = (max_position or 0) + 1
            else:
                # Check if position already exists
                existing_at_position = Category.objects.filter(position=self.position).exists()
                if existing_at_position:
                    # Shift existing categories with position >= self.position
                    Category.objects.filter(position__gte=self.position).update(
                        position=models.F('position') + 1
                    )
        else:  # Existing category
            old_category: Category = Category.objects.get(pk=self.pk)
            if old_category.position != self.position:
                if self.position == 0:
                    # Move to end
                    max_position = Category.objects.exclude(pk=self.pk).aggregate(max_pos=models.Max('position'))['max_pos']
                    self.position = (max_position or 0) + 1
                else:
                    # Check for position conflicts and resolve using creation date
                    conflicting_category = Category.objects.filter(
                        position=self.position
                    ).exclude(pk=self.pk).first()
                    
                    if conflicting_category:
                        if self.position < old_category.position:
                            # Moving up - shift categories between new and old position down
                            Category.objects.filter(
                                position__gte=self.position,
                                position__lt=old_category.position
                            ).exclude(pk=self.pk).update(position=models.F('position') + 1)
                        else:
                            # Moving down - shift categories between old and new position up
                            Category.objects.filter(
                                position__gt=old_category.position,
                                position__lte=self.position
                            ).exclude(pk=self.pk).update(position=models.F('position') - 1)
                            
        # Ensure no duplicate positions exist after save
        super(Category, self).save(*args, **kwargs)
        
        # Post-save cleanup: fix any remaining position conflicts using creation date
        self._fix_position_conflicts()
    
    def _fix_position_conflicts(self):
        """Fix position conflicts by using creation date as tiebreaker"""
        # Get all categories with duplicate positions
        from django.db.models import Count
        duplicate_positions = Category.objects.values('position').annotate(
            count=Count('position')
        ).filter(count__gt=1).values_list('position', flat=True)
        
        for position in duplicate_positions:
            # Get categories at this position, ordered by creation date
            categories_at_position = Category.objects.filter(
                position=position
            ).order_by('created_at')
            
            # Keep the first (oldest) category at this position
            # Move others to the next available positions
            for i, category in enumerate(categories_at_position[1:], 1):
                max_position = Category.objects.aggregate(
                    max_pos=models.Max('position')
                )['max_pos'] or 0
                category.position = max_position + i
                # Use update to avoid triggering save() again
                Category.objects.filter(pk=category.pk).update(
                    position=category.position
                )
    
    
    
class SocialMediaAccount(models.Model):

    VERIFICATION_STATUS_CHOICES = [
        ('verified', 'Verified'),
        ('not_verified', 'Not Verified'),
        ('pending', 'Pending'),
    ]

    title = models.CharField(max_length=100, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(help_text="A brief description of the social media account.")
    followers_count = models.PositiveIntegerField(default=0, help_text="The number of followers on the account.", null=True, blank=True)
    following_count = models.PositiveIntegerField(default=0, help_text="The number of following on the account.", null=True, blank=True)
    account_age = models.CharField(max_length=4, blank=True, null=True)
    verification_status = models.CharField(max_length=12, choices=VERIFICATION_STATUS_CHOICES, blank=True, null=True)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="The price of the account. It is in Naira."
    )
    # stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    position = models.PositiveIntegerField(default=0)
    position_created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['position', 'position_created_at']
    
    def __str__(self):
        return f"{self.social_media} - {self.title} - {self.followers_count} followers"
    
    def save(self, *args, **kwargs):
        # Handle position assignment with date-based conflict resolution
        if not self.pk:  # New social_media_acct
            if self.position == 0:
                # Get the highest position and add 1
                max_position = SocialMediaAccount.objects.aggregate(max_pos=models.Max('position'))['max_pos']
                self.position = (max_position or 0) + 1
            else:
                # Check if position already exists
                existing_at_position = SocialMediaAccount.objects.filter(position=self.position).exists()
                if existing_at_position:
                    # Shift existing categories with position >= self.position
                    SocialMediaAccount.objects.filter(position__gte=self.position).update(
                        position=models.F('position') + 1
                    )
        else:  # Existing social_media_acct
            old_social_media_acct: SocialMediaAccount = SocialMediaAccount.objects.get(pk=self.pk)
            if old_social_media_acct.position != self.position:
                if self.position == 0:
                    # Move to end
                    max_position = SocialMediaAccount.objects.exclude(pk=self.pk).aggregate(max_pos=models.Max('position'))['max_pos']
                    self.position = (max_position or 0) + 1
                else:
                    # Check for position conflicts and resolve using creation date
                    conflicting_social_media_acct = SocialMediaAccount.objects.filter(
                        position=self.position
                    ).exclude(pk=self.pk).first()
                    
                    if conflicting_social_media_acct:
                        if self.position < old_social_media_acct.position:
                            # Moving up - shift categories between new and old position down
                            SocialMediaAccount.objects.filter(
                                position__gte=self.position,
                                position__lt=old_social_media_acct.position
                            ).exclude(pk=self.pk).update(position=models.F('position') + 1)
                        else:
                            # Moving down - shift categories between old and new position up
                            SocialMediaAccount.objects.filter(
                                position__gt=old_social_media_acct.position,
                                position__lte=self.position
                            ).exclude(pk=self.pk).update(position=models.F('position') - 1)
                            
        # Ensure no duplicate positions exist after save
        super(SocialMediaAccount, self).save(*args, **kwargs)
        
        # Post-save cleanup: fix any remaining position conflicts using creation date
        self._fix_position_conflicts()
    
    def _fix_position_conflicts(self):
        """Fix position conflicts by using creation date as tiebreaker"""
        # Get all categories with duplicate positions
        from django.db.models import Count
        duplicate_positions = SocialMediaAccount.objects.values('position').annotate(
            count=Count('position')
        ).filter(count__gt=1).values_list('position', flat=True)
        
        for position in duplicate_positions:
            # Get categories at this position, ordered by creation date
            categories_at_position: list[SocialMediaAccount] = SocialMediaAccount.objects.filter(
                position=position
            ).order_by('position_created_at')
            
            # Keep the first (oldest) social_media_acct at this position
            # Move others to the next available positions
            for i, social_media_acct in enumerate(categories_at_position[1:], 1):
                max_position = SocialMediaAccount.objects.aggregate(
                    max_pos=models.Max('position')
                )['max_pos'] or 0
                social_media_acct.position = max_position + i
                # Use update to avoid triggering save() again
                SocialMediaAccount.objects.filter(pk=social_media_acct.pk).update(
                    position=social_media_acct.position
                )
    
    @property
    def social_media(self):
        return self.category.name if self.category else ''

    @property
    def stock(self):
        return Log.objects.filter(account=self, is_active=True).count()

    @property
    def is_in_stock(self):
        return self.stock > 0

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_number}"

    def generate_order_number(self):
        return f"ORD-{uuid.uuid4().hex[:8]}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    @property
    def disp_order_number(self):
        return f"{self.order_number}".lower().replace('ord-', '')

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    account = models.ForeignKey(SocialMediaAccount, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity}x {self.account.title} - {self.account.social_media}"

    @property
    def subtotal(self):
        return self.quantity * self.price

    def get_allocated_logs(self):
        if self.quantity <= 0:
            return []

        # check if the item already has allocated logs
        if Log.objects.filter(order_item=self).exists():
            return Log.objects.filter(order_item=self)

        # allocate logs (quantity, for example 10 for 10 logs) to order item and mark them as inactive
        new_logs = Log.objects.filter(account=self.account, is_active=True)[:self.quantity]
        for log in new_logs:
            log.order_item = self
            log.is_active = False
            log.save()
        
        return new_logs
        

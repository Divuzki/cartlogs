from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class Log(models.Model):
    account = models.ForeignKey("marketplace.SocialMediaAccount", on_delete=models.CASCADE)
    log_data = models.TextField()
    is_active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Log for {self.account}"

class SocialMediaAccount(models.Model):
    SOCIAL_MEDIA_CHOICES = [
        # in a tupe [0] is the value and [1] is the display
        ('OJ’s SPECIAL STOCK🌚💯','OJ’s SPECIAL STOCK🌚💯'),
        ('Texting💬', 'Texting💬'),
        ('twitter', 'Twitter'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('snapchat', 'Snapchat'),
        ('reddit', 'Reddit'),
        ('tiktok', 'TikTok'),
        ('vpn', 'VPN'),
        ('tools', 'Tools'),
        ('email', 'Email'),
        ('streaming', 'Streaming'),
        ('others', 'Others'),
    ]

    VERIFICATION_STATUS_CHOICES = [
        ('verified', 'Verified'),
        ('not_verified', 'Not Verified'),
        ('pending', 'Pending'),
    ]

    title = models.CharField(max_length=100, blank=True, null=True)

    social_media = models.CharField(max_length=20, choices=SOCIAL_MEDIA_CHOICES)
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

    def __str__(self):
        return f"{self.social_media} - {self.title} - {self.followers_count} followers"

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

    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
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

class Payment(models.Model):
    order = models.ForeignKey(Order, related_name='payments', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20)
    payment_data = models.JSONField(default=dict)  # Stores payment gateway response
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.transaction_id} for Order {self.order.order_number}"

from django.contrib import admin
from .models import SocialMediaAccount, Order, OrderItem, Payment, Log

class SocialMediaAccountAdmin(admin.ModelAdmin):
    list_display = ('social_media', 'title', 'followers_count', 'price', 'is_active')
    search_fields = ('social_media', 'title')
    list_filter = ('social_media', 'is_active')
    ordering = ('social_media',)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'total_amount', 'created_at')
    search_fields = ('order_number',)
    list_filter = ('status',)
    ordering = ('-created_at',)

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'account', 'quantity', 'price')
    search_fields = ('order__order_number',)
    ordering = ('order',)

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'order', 'amount', 'status', 'created_at')
    search_fields = ('transaction_id',)
    list_filter = ('status',)
    ordering = ('-created_at',)

class LogAdmin(admin.ModelAdmin):
    list_display = ('account', 'timestamp')
    search_fields = ('account__social_media',)
    ordering = ('-timestamp',)

# Register the models with the admin site
admin.site.register(SocialMediaAccount, SocialMediaAccountAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Log, LogAdmin)
from django.contrib import admin
from .models import SocialMediaAccount, Order, OrderItem, Log, Category

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


class LogInline(admin.TabularInline):
    model = Log
    extra = 0  # Set to 0 to prevent adding extra logs
    readonly_fields = ('order_item', 'account', 'timestamp', 'is_active')  # Make fields readonly
    fields = ('order_item', 'account', 'timestamp', 'is_active')  # Specify the order of fields
    can_delete = False  # Prevent deleting logs

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'account', 'quantity', 'price')
    search_fields = ('order__order_number',)
    ordering = ('order',)
    inlines = [LogInline]

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'order', 'amount', 'status', 'created_at')
    search_fields = ('transaction_id',)
    list_filter = ('status',)
    ordering = ('-created_at',)

class LogAdmin(admin.ModelAdmin):
    list_display = ('account', 'timestamp')
    search_fields = ('account__social_media',)
    ordering = ('-timestamp',)
    
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    ordering = ('name',)
    # slug automatically generated
    prepopulated_fields = {'slug': ('name',)}

# Register the models with the admin site
admin.site.register(SocialMediaAccount, SocialMediaAccountAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Log, LogAdmin)
admin.site.register(Category, CategoryAdmin)
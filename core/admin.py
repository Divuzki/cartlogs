from django.contrib import admin
from .models import Transaction, Wallet

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'type', 'amount', 'payment_gateway', 'status', 'created_at')
    list_filter = ('type', 'payment_gateway', 'status', 'created_at')
    search_fields = ('wallet__user__username', 'payment_reference', 'description')
    readonly_fields = ('payment_reference',)
    ordering = ('-created_at',)
    
    def save_model(self, request, obj, form, change):
        # Generate a unique reference if this is a new transaction
        if not change and not obj.payment_reference:
            import uuid
            obj.payment_reference = f"admin-{uuid.uuid4().hex[:12]}"
        super().save_model(request, obj, form, change)

    def mark_as_success(self, request, queryset):
        queryset.update(status='success')
    mark_as_success.short_description = 'Mark selected transactions as successful'

    actions = ['mark_as_success']

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__username',)
    readonly_fields = ('balance',)

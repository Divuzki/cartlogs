from django.contrib import admin
from .models import Transaction, Wallet
from django import forms

class TransactionAdminForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit the number of wallets shown in the dropdown
        self.fields['wallet'].queryset = Wallet.objects.all().select_related('user')[:100]  # Adjust the limit as needed

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    form = TransactionAdminForm
    list_display = ('wallet', 'type', 'amount', 'payment_gateway', 'status', 'created_at')
    list_filter = ('type', 'payment_gateway', 'status', 'created_at')
    search_fields = ('wallet__user__username', 'payment_reference', 'description')
    readonly_fields = ('payment_reference',)
    ordering = ('-created_at',)
    raw_id_fields = ('wallet',)  # Use a search input instead of dropdown
    
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

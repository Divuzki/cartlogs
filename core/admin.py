from django.contrib import admin
from .models import Wallet, Transaction

class TransactionInline(admin.TabularInline):
    model = Transaction
    readonly_fields = ('payment_reference', 'payment_gateway', 'wallet', 'amount', 'type', 'description', 'created_at')
    extra = 0

class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    inlines = [TransactionInline]

admin.site.register(Wallet, WalletAdmin)

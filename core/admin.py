from django.contrib import admin
from .models import Wallet, Transaction

class TransactionInline(admin.TabularInline):
    model = Transaction
    readonly_fields = ('wallet', 'amount', 'description', 'status', 'created_at')
    extra = 0

class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    inlines = [TransactionInline]

admin.site.register(Wallet, WalletAdmin)

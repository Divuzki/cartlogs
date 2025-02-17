import os
import django
from datetime import datetime
from decimal import Decimal

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")
django.setup()

from marketplace.models import AccountCategory, SocialMediaAccount, Order, OrderItem, Payment, Log

def populate():
    # Create Account Categories
    category1 = AccountCategory.objects.create(name="Personal Accounts", description="Accounts for personal use.")
    category2 = AccountCategory.objects.create(name="Business Accounts", description="Accounts for business purposes.")

    # Create Social Media Accounts
    account1 = SocialMediaAccount.objects.create(
        category=category1,
        social_media='twitter',
        account_type='Personal',
        description='Personal Twitter account with a good following.',
        followers_count=1500,
        following_count=300,
        account_age='2020',
        verification_status='verified',
        price=Decimal('200000.00'),
        stock=10,
        is_active=True
    )

    account2 = SocialMediaAccount.objects.create(
        category=category2,
        social_media='facebook',
        account_type='Business',
        description='Business Facebook account for marketing.',
        followers_count=5000,
        following_count=1000,
        account_age='2013',
        verification_status='not_verified',
        price=Decimal('500000.00'),
        stock=5,
        is_active=True
    )

    # Create Orders
    order1 = Order.objects.create(
        user=None,  # Assuming you have a user object to assign here
        order_number='ORD-1234567878',
        status='completed',
        payment_status='paid',
        total_amount=Decimal('700000.00'),
        payment_method='Credit Card',
        payment_reference='PAY-1234756',
        notes='First order for testing.',
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # Create Order Items
    OrderItem.objects.create(order=order1, account=account1, quantity=1, price=Decimal('20000.00'))
    OrderItem.objects.create(order=order1, account=account2, quantity=1, price=Decimal('50000.00'))

    # Create Payments
    Payment.objects.create(
        order=order1,
        amount=Decimal('700000.00'),
        payment_method='Credit Card',
        transaction_id='TXN-12345876',
        status='paid',
        payment_data={'status': 'success'},
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    # Create Logs
    Log.objects.create(account=account1, log_data='Log entry for Twitter account.', timestamp=datetime.now())
    Log.objects.create(account=account2, log_data='Log entry for Facebook account.', timestamp=datetime.now())

if __name__ == "__main__":
    populate()
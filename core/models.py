from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from numerize.numerize import numerize

class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = (
        ('unknown', 'Unknown'),
        ('credit', 'Credit'),
        ('debit', 'Debit'),
        ('refund', 'Refund'),
    )

    TRANSACTION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    )

    TRANSACTION_PAYMENT_GATEWAY_CHOICES = (
        ('unknown', 'Unknown'),
        ('korapay', 'Korapay'),
        ('wallet', 'Wallet'),
        ('manual', 'Manual Transfer'),
    )

    payment_reference = models.CharField(max_length=100, blank=True, null=True, editable=False, unique=True)

    payment_gateway = models.CharField(max_length=20, choices=TRANSACTION_PAYMENT_GATEWAY_CHOICES, default='unknown')

    wallet = models.ForeignKey("core.Wallet", on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES, default='unknown')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return self.wallet.user.username

    class Meta:
        ordering = ['-created_at']
    @property
    def display_amount(self):
        return numerize(self.amount)

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, editable=False)

    def __str__(self):
        try:
            return self.user.username + f" ({self.user.email})"
        except:
            return self.balance
    
    @property
    def display_balance(self):
        return numerize(self.balance)

    @property
    def total_spent(self):
        return Transaction.objects.filter(wallet=self).aggregate(models.Sum('amount'))['amount__sum'] or 0

    def credit(self, amount: Decimal, transaction=None):
        """
        credit the wallet

        Args:
            amount (Decimal): the amount to credit

        Raises:
            ValueError: if the new balance is less than 0
        """
        if self.balance + amount < 0:
            raise ValueError("Insufficient funds")
        self.balance += amount

        # check if transaction exists
        if transaction:
            transaction.amount = amount
            transaction.status = 'success'
            transaction.description = "Credited"
            transaction.save()
        else:
            # create transaction
            Transaction.objects.create(wallet=self, amount=amount, type='credit', status='success', description="Credited")
        self.save()

    def debit(self, amount: Decimal, transaction=None):
        """
          debit the wallet

        Args:
            amount (Decimal): the amount to debit

        Raises:
            ValueError: if the new balance is less than 0
        """
        if self.balance - amount < 0:
            raise ValueError("Insufficient funds")
        self.balance -= amount

        # check if transaction exists
        if transaction:
            transaction.amount = amount
            transaction.status = 'success'
            transaction.description = "Debited"
            transaction.save()
        else:
            # create transaction
            Transaction.objects.create(wallet=self, amount=amount, type='debit', status='success', description="Debited")
        self.save()

    def refund(self, amount: Decimal, transaction_id: str):
        """
        refund the wallet

        Args:
            amount (Decimal): the amount to refund
            transaction_id (str): the id of the transaction to refund

        Raises:
            ValueError: if the transaction is not a debit
        """
        transaction = Transaction.objects.get(id=transaction_id)
        # check if the transaction is a debit
        if transaction.type != 'debit':
            raise ValueError("Transaction is not a debit")

        self.balance += amount
        # create transaction
        Transaction.objects.create(wallet=self, amount=amount, type='refund', status='success', description="Refunded")
        self.save()



@receiver(post_save, sender=User)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        if not Wallet.objects.filter(user=instance).exists():
            Wallet.objects.create(user=instance)
            instance.save()

@receiver(post_save, sender=Transaction)
def update_transaction(sender, instance, created, **kwargs):
    # Check if it's a manual transaction and status is success and not already processing
    if instance.payment_gateway == 'manual' and instance.status == 'success' and not hasattr(instance, '_processing'):
        instance._processing = True
        
        # Generate payment reference if not exists
        if instance.payment_reference is None:
            import uuid
            instance.payment_reference = str(uuid.uuid4().hex[:8])
        
        # Handle both credit and refund type transactions
        if instance.type in ['credit', 'refund']:
            instance.wallet.credit(instance.amount, transaction=instance)
        
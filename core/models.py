from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from numerize.numerize import numerize

class Transaction(models.Model):
    wallet = models.ForeignKey("core.Wallet", on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.wallet.user.username

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.user.username

    def display_balance(self):
        return

    def add_funds(self, amount):
        self.balance += amount
        self.save()

    def remove_funds(self, amount):
        self.balance -= amount
        self.save()

    def get_total_spent(self):
        return Transaction.objects.filter(wallet=self).aggregate(models.Sum('amount'))['amount__sum'] or 0

    def get_total_earned(self):
        return Transaction.objects.filter(wallet=self).aggregate(models.Sum('amount'))['amount__sum'] or 0



# signals to create transaction when wallet balance is updated
@receiver(post_save, sender=Wallet)
def create_transaction(sender, instance, created, **kwargs):
    if created or instance.balance > 0:
        Transaction.objects.create(wallet=instance, amount=instance.balance, description="Initial balance")
        instance.balance = 0
        instance.save() 
    
    if instance.balance < 0:
        Transaction.objects.create(wallet=instance, amount=instance.balance, description="Withdrawal")
        instance.balance = 0
        instance.save()

@receiver(post_save, sender=User)
def create_wallet(sender, instance, created, **kwargs):
    if created:
        if not Wallet.objects.filter(user=instance).exists():
            Wallet.objects.create(user=instance)
            instance.save() 
import logging

from django.http import HttpResponse
from decimal import Decimal
from .models import Wallet, Transaction
from django.conf import settings
from django.core.mail import EmailMessage

def caluate_gateway_fee(order_price):
    gateway_fee = 0
    if order_price <= 2500:
        gateway_fee = 100
    elif order_price > 2500:
        gateway_fee = int(Decimal(order_price) * Decimal(0.025) + 100)
    return Decimal(gateway_fee)

class ProcessKorapayPayment:
    """
    This class is used to process the payment based on the event type.
    """

    def __init__(self, event_type, event_data):
        self.event_type = event_type
        self.event_data = event_data
        self.response_data = {}

    def process_payment(self):
        if self.event_type == "charge.dispute.create":
            return self.charge_dispute_create()
        if self.event_type == "charge.dispute.remind":
            return self.charge_dispute_remind()
        if self.event_type == "charge.dispute.resolve":
            return self.charge_dispute_resolve()
        if self.event_type == "charge.success":
            return self.charge_success()
        if self.event_type == "charge.failed":
            return self.charge_failed()
        else:
            return HttpResponse("Invalid event type", status=400)

    def charge_dispute_create(self):

        email = EmailMessage(
            "Charge Dispute",
            f"Charge Dispute\n\n{self.event_data}",
            settings.EMAIL_HOST_USER,
            ["cartlogs@yopmail.com"],
        )
        email.send()

        return HttpResponse("Charge Dispute", status=200)

    def charge_dispute_remind(self):

        email = EmailMessage(
            "Charge Dispute Remind",
            f"Charge Dispute Remind\n\n{self.event_data}",
            settings.EMAIL_HOST_USER,
            ["cartlogs@yopmail.com", "divuzki@gmail.com"],
        )
        email.send()
        return HttpResponse("Charge Dispute Remind", status=200)

    def charge_dispute_resolve(self):

        email = EmailMessage(
            "Charge Dispute Resolve",
            f"Charge Dispute Resolve\n\n{self.event_data}",
            settings.EMAIL_HOST_USER,
            ["cartlogs@yopmail.com"],
        )
        email.send()
        return HttpResponse("Charge Dispute Resolve", status=200)

    def charge_success(self):
        try:
            # Get reference and amount
            reference = self.event_data["reference"]
            
            # Get transaction
            transaction: Transaction = Transaction.objects.get(payment_reference=reference)
   
            # Get wallet
            wallet: Wallet = transaction.wallet
            if transaction.status == 'success':
                return HttpResponse("Charge Success", status=200)
            wallet.credit(transaction.amount, transaction)
            wallet.save()
            
            return HttpResponse("Charge Success", status=200)
        except Exception as e:
            return HttpResponse("Charge Failed", status=500)

    def charge_failed(self):
        try:
            # Get reference and amount
            reference = self.event_data["reference"]

            # Get transaction and update status
            transaction: Transaction = Transaction.objects.get(payment_reference=reference)
            
            transaction.status = 'failed'
            transaction.description = "Charge Failed"
            transaction.save()
            return HttpResponse("Charge Failed", status=200)
        except Exception as e:
            logging.error(e)
        return HttpResponse("Charge Failed", status=500)
             
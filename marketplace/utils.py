import logging

from django.http import HttpResponse
from .models import Order, OrderItem, Payment, Log, SocialMediaAccount
from decimal import Decimal

from django.conf import settings
from django.core.mail import EmailMessage


class ProcessPayment:
    """
    This class is used to process the payment based on the event type.
    """

    def __init__(self, event_type, event_data):
        self.event_type = event_type
        self.event_data = event_data
        self.response_data = {}

    def process_payment(self):
        logging.info("event_type", self.event_type)
        if self.event_type == "charge.dispute.create":
            return self.charge_dispute_create()
        if self.event_type == "charge.dispute.remind":
            return self.charge_dispute_remind()
        if self.event_type == "charge.dispute.resolve":
            return self.charge_dispute_resolve()
        if self.event_type == "charge.success":
            return self.charge_success()
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
        # get the values from event_data
        reference = self.event_data["reference"]
        payment_status = self.event_data["status"]
        try:
            order_payment_method = self.event_data["authorization"]["channel"]
        except KeyError:
            order_payment_method = "unknown"

        order_price = self.event_data["amount"]
        # convert the order_price to a decimal and divide it by 100
        order_price = Decimal(order_price) / 100

        # get the order from the database
        print(reference)
        order_qs: list[Order] = (
            Order.objects.select_related("user")
            .filter(payment_reference=reference)
            .exclude(payment_status="paid")
        )

        # check if the order exists
        if not order_qs.exists():
            return HttpResponse("Order does not exist", status=404)

        order: Order = order_qs.first()
        order.payment_method = order_payment_method

        if "success" == payment_status:
            # create a payment object
            Payment.objects.create(
                order=order,
                amount=order_price,
                payment_method=order_payment_method,
                transaction_id=reference,
                status=payment_status,
                payment_data=self.event_data,
            )

            order.payment_status = "paid"
            order.status = "completed"
            order.save()

            logs_list = []

            

            order_items: list[OrderItem] = OrderItem.objects.filter(order=order)
            social_media_accounts: list[SocialMediaAccount] = SocialMediaAccount.objects.filter(id__in=[item.account.id for item in order_items])
            for account in social_media_accounts:
                
                # if the account has reached 0 stock, mark it as inactive
                if account.stock == 0:
                    account.is_active = False

                order_qty = sum(item.quantity for item in order_items.filter(account=account))
                    
                # get the log related to this account and mark it as inactive
                log = Log.objects.filter(account=account, is_active=True).order_by("-timestamp")[:order_qty].first()
                if not log:
                    # send an email to the user
                    print("No Logs Left")
                    email = EmailMessage(
                        "No Logs Left",
                        f"No Logs Left\n\n{account.title}, {account.social_media}, ID: {account.id}. Please contact the admin.",
                        settings.EMAIL_HOST_USER,
                        [order.user.email],
                    )
                    email.send()
                    continue
                logs_list.append(log.log_data)
                log.is_active = False
                log.save()
                account.save()

            # send the logs_list to the user by email
            email = EmailMessage(
                "Logs From Cart Logs",
                f"Logs\n\n{logs_list}",
                settings.EMAIL_HOST_USER,
                [order.user.email],
            )
            email.send()
            print("Logs sent to user")
            

            return HttpResponse("Payment successful", status=200)

   
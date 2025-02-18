import logging

from django.http import HttpResponse
from .models import Order, Payment
from decimal import Decimal

from django.conf import settings
from django.db.models import Q


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
        from django.core.mail import EmailMessage

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
            order.save()
            return HttpResponse("Payment successful", status=200)

   
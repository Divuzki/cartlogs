from django.shortcuts import render, redirect
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
import json
from .models import SocialMediaAccount, Order, OrderItem
from numerize.numerize import numerize

from django.contrib.auth.decorators import login_required
from django.conf import settings


PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY


def view_all(request, social_media):
    # Fetch accounts from the database
    accounts: list[SocialMediaAccount] = SocialMediaAccount.objects.filter(is_active=True, social_media=social_media)
    accounts_data = []
    
    for account in accounts:
        # format followers count to 1000 to 1k or 5000
        followers_count = account.followers_count
        try:
            formatted_followers = numerize(followers_count, 2)
        except:
            formatted_followers = followers_count
        
        accounts_data.append({
            'id': account.id,
            'title': f"{account.social_media} | {formatted_followers} followers" if not account.title else account.title,
            'description': account.description,
            'price': account.price,
            'stock': account.stock,
            'inStock': account.is_in_stock,  # Use the property to check stock
            'verification_status': f"{account.verification_status}".replace('_', ' '),
            'account_age': account.account_age,
        })
    
    return render(request, 'view_all.html', {'accounts': accounts_data, 'social_media': social_media})

    
def marketplace(request):
    social_media_accounts: list[SocialMediaAccount] = SocialMediaAccount.objects.filter(is_active=True)
    grouped_accounts = []

    # Group accounts by social media
    social_media_dict = {}
    for account in social_media_accounts:
        social_media = account.social_media
        if social_media not in social_media_dict:
            social_media_dict[social_media] = []
        followers_count = account.followers_count
        try:
            formatted_followers = numerize(followers_count, 2)
        except:
            formatted_followers = followers_count
        social_media_dict[social_media].append({
            'id': account.id,
            'title': f"{account.social_media} | {formatted_followers} followers" if not account.title else account.title,
            'description': account.description,
            'price': account.price,
            'stock': account.stock,
            'inStock': account.is_in_stock,  # Use the property to check stock
            'verification_status': f"{account.verification_status}".replace('_', ' '),
            'account_age': account.account_age,
        })

    # Convert to the desired structure
    for name, accounts in social_media_dict.items():
        grouped_accounts.append({
            "name": name,
            "id": name,
            "accounts": accounts[:8]  # Limit to 8 accounts per social media
        })

    return render(request, 'marketplace.html', {'grouped_accounts': grouped_accounts})

@login_required
@require_POST
def checkout(request):
    
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method'
        }, status=405)

    try:
        cart_data = json.loads(request.POST.get('cart_data', '[]'))
        
        # Validate the cart data
        if not cart_data:
            return JsonResponse({
                'status': 'error',
                'message': 'No items in cart'
            }, status=400)

        # Create an order in your database
        order: Order = Order.objects.create(
            user=request.user,  # Assuming you have a user object
            total_amount=Decimal('0.00'),  # Initialize with a default value
            status='pending'  # You can set this based on your workflow
        )

        # Create order items for each cart item
        for item_data in cart_data:
            account: SocialMediaAccount = SocialMediaAccount.objects.get(id=item_data['id'])
            # validate stock
            if account.stock < item_data['quantity']:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Insufficient stock for {account.social_media}'
                }, status=400)
            
            order_item: OrderItem = OrderItem.objects.create(
                order=order,
                account=account,
                quantity=item_data['quantity'],
                price=account.price
            )
            order.total_amount += order_item.subtotal
            order.save()
        # Redirect to checkout page with order data
        return redirect('marketplace:after_checkout', order_id=order.id)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

import requests
from django.conf import settings  # To access environment variables

def generate_payment_link(callback_url, amount, email):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "amount": str(int(amount * 100)),  # Paystack expects amount in kobo
        "callback_url": callback_url,
        "metadata": {
            "cancel_action": callback_url
        }
    }

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        data = response.json().get('data', {})
        return data.get('authorization_url'), data.get('reference')  # Return both URL and reference
    else:
        # Handle error appropriately
        return None, None

def verify_payment(reference):
    """
    #!/bin/sh
url="https://api.paystack.co/transaction/verify/{reference}"
authorization="Authorization: Bearer YOUR_SECRET_KEY"

curl "$url" -H "$authorization" -X GET
    """
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json().get('data', {})
        return data['status']
    else:
        # Handle error appropriately
        return None

def caluate_gateway_fee(order_price):
        gateway_fee = 0
        if order_price <= 2500:
            gateway_fee = 100
        elif order_price > 2500:
            gateway_fee = order_price * Decimal(0.025) + 100
        return gateway_fee

@login_required
@require_GET
def after_checkout(request, order_id):

    order: Order = Order.objects.get(id=order_id)

    # check of user has already paid for the order
    if order.payment_status == 'paid':
        return render(request, 'after_checkout.html', {'order': order, 'is_paid': True})

    if order.payment_reference:
        # verify the payment
        payment_status = verify_payment(order.payment_reference)
        if payment_status == 'success':
            order.payment_status = 'paid'
            order.save()
            return render(request, 'after_checkout.html', {'order': order, 'is_paid': True})
        

    site_url = request.build_absolute_uri('/')
    callback_url = site_url + 'after_checkout/' + str(order_id) + '/'
    
    # Initialize payment link
    order_total = order.total_amount + caluate_gateway_fee(order.total_amount)
    payment_link, payment_reference = generate_payment_link(callback_url, order_total, request.user.email)

    # Save the payment reference in the order
    order.payment_reference = payment_reference
    order.save()


    return render(request, 'after_checkout.html', {'order': order, 'payment_link': payment_link})



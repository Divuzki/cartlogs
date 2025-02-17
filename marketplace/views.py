from django.shortcuts import render, redirect
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
import json
from .models import SocialMediaAccount, Order, OrderItem
from numerize.numerize import numerize


def marketplace(request):
    # Fetch accounts from the database
    accounts: list[SocialMediaAccount] = SocialMediaAccount.objects.filter(is_active=True)  # Only get active accounts
    accounts_data = []
    
    for account in accounts:
        # format followers count to 1000 to 1k or 5000
        followers_count = account.followers_count
        formatted_followers = numerize(followers_count, 2)
        
        accounts_data.append({
            'id': account.id,
            'title': f"{account.social_media} | {formatted_followers} followers",
            'description': account.description,
            'price': account.price,
            'stock': account.stock,
            'inStock': account.is_in_stock,  # Use the property to check stock
            'verification_status': account.verification_status,
            'account_age': account.account_age,
            'type': account.category.name
        })
    
    return render(request, 'marketplace.html', {'accounts': accounts_data})

@require_POST
def checkout(request):
    # check if user is authenticated, if not redirect to login page
    if not request.user.is_authenticated:
        return redirect('auth_page')
    
    if request.method != 'POST':
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid request method'
        }, status=405)

    try:
        cart_data = json.loads(request.POST.get('cart_data', '[]'))
        print(cart_data)
        
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

def generate_payment_link(amount, email):
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "amount": str(int(amount * 100)),  # Paystack expects amount in kobo
    }

    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        data = response.json().get('data', {})
        return data.get('authorization_url'), data.get('reference')  # Return both URL and reference
    else:
        # Handle error appropriately
        return None, None

@require_GET
def after_checkout(request, order_id):
    # Check if user is authenticated, if not redirect to login page
    if not request.user.is_authenticated:
        return redirect('auth_page')

    order: Order = Order.objects.get(id=order_id)

    # Initialize payment link
    payment_link, payment_reference = generate_payment_link(order.total_amount, request.user.email)

    # Save the payment reference in the order
    order.payment_reference = payment_reference
    order.save()

    return render(request, 'after_checkout.html', {'order': order, 'payment_link': payment_link})
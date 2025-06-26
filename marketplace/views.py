from django.shortcuts import render, redirect, get_object_or_404
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET, require_http_methods
import json
from .models import SocialMediaAccount, Order, OrderItem
from numerize.numerize import numerize
from core.models import Transaction, Wallet
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth import authenticate

from django.db.models import Sum


import logging

logger = logging.getLogger(__name__)


def view_all(request, social_media):
    # Fetch accounts from the database
    accounts: list[SocialMediaAccount] = SocialMediaAccount.objects.filter(is_active=True, category__slug=social_media)
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

    from .models import Category
    # Get all categories ordered by position
    categories: list[Category] = Category.objects.all()
    
    # Create a mapping of category name to their position
    social_media_order = {cat.name: cat.position for cat in categories}
    
    # Sort the social_media_dict based on the category positions
    social_media_dict = dict(sorted(
        social_media_dict.items(),
        key=lambda item: social_media_order.get(item[0], float('inf'))
    ))
    

    # Convert to the desired structure
    for name, accounts in social_media_dict.items():
        grouped_accounts.append({
            "name": name,
            "id": name,
            "accounts": accounts[:8]  # Limit to 8 accounts per social media
        })

    return render(request, 'marketplace.html', {'grouped_accounts': grouped_accounts})

@login_required
@require_http_methods(["GET"])
def orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    total_orders = orders.count()
    total_spent = orders.filter(status="completed").aggregate(Sum('total_amount'))['total_amount__sum'] or 0

    context = {
        'orders': orders,
        'total_orders': total_orders,
        'total_spent': total_spent,
    }
    return render(request, 'orders.html', context)

@login_required
@require_http_methods(["GET"])
def order_details(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'order_details.html', {'order': order})

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
            item_data['quantity'] = int(item_data['quantity'])
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



@login_required
@require_GET
def after_checkout(request, order_id):

    order: Order = Order.objects.get(id=order_id)

    # check of user has already paid for the order
    if order.status == 'completed':
        return render(request, 'after_checkout.html', {'order': order, 'is_paid': True})


    # site_url = request.build_absolute_uri('/')
    # callback_url = site_url + 'after_checkout/' + str(order_id) + '/'
    if not order.transaction:
        order.status = 'pending'
        order.save()


    return render(request, 'after_checkout.html', {'order': order})

@login_required
def password_confirm(request, order_number):
    """
    Display the password confirmation page for a payment
    """
    try:
        
        order: Order = Order.objects.get(order_number=order_number)

        if not order.transaction:
            new_pending_transaction: Transaction = Transaction.objects.create(
                payment_reference = order.order_number,
                payment_gateway = 'wallet',
                wallet = order.user.wallet,
                type = 'debit',
                amount = order.total_amount,
                description = "Pending payment for order #{}".format(order.order_number),
            )
            new_pending_transaction.save()
            order.transaction = new_pending_transaction
            order.status = 'processing'
            order.save()
        
        context = {
            'amount': order.total_amount,
            'order_number': order.order_number
        }
        return render(request, 'confirm_payment.html', context)
    except Order.DoesNotExist:
        return redirect('marketplace:payment_error')

@login_required
@require_http_methods(["POST"])
def confirm_payment(request):
    """
    Handle the transaction confirmation
    """
    try:
        data = json.loads(request.body)
        order_number = data.get('order_number')

        # Get the transaction
        try:
            transaction: Transaction = Transaction.objects.get(
                payment_reference=order_number
            )
        except Transaction.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'errors': {'general': 'Transaction not found, Please try again'}
            }, status=404)

        if transaction.status != 'pending':
            return JsonResponse({
                'status': 'error',
                'errors': {'general': 'Transaction already processed or cancelled, Please try again'}
            }, status=400)

        transaction_wallet: Wallet = transaction.wallet

        # Check wallet balance
        if transaction_wallet.balance < transaction.amount:
            return JsonResponse({
                'status': 'error',
                'redirect_url': reverse('add_funds'),
                'errors': {'general': 'Insufficient Funds in Wallet, redirecting to topup page...'}
            }, status=400)

        # Process payment
        try:
            # Deduct from wallet
            transaction_wallet.debit(transaction.amount, transaction)

            # get order
            order: Order = Order.objects.get(order_number=order_number)

            # allocate logs to each order item
            for order_item in order.items.all():
                order_item.get_allocated_logs()

            order.status = 'completed'
            order.save()

            return JsonResponse({
                'status': 'success',
                'redirect_url': reverse('marketplace:after_checkout', args=[order.id])
            })
        except Exception as e:
            print(e)
            return JsonResponse({
                'status': 'error',
                'errors': {'general': 'Payment processing failed'}
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'errors': {'general': 'Invalid request format'}
        }, status=400)
    except Exception as e:
        logging.error(e)
        return JsonResponse({
            'status': 'error',
            'errors': {'general': 'An unexpected error occurred'}
        }, status=500)

@login_required
def cancel_order(request, order_number):
    """
    Cancel a order
    """
    try:
        order = Order.objects.get(
            order_number=order_number,
            user=request.user
        )
        order.status = 'cancelled'
        order.save()

        # make order.transaction as cancelled
        order.transaction.status = 'cancelled'
        order.transaction.save()

        return redirect('marketplace:order_details', order_id=order.id)
    except Order.DoesNotExist:
        return redirect('marketplace:order_details', order_id=order.id)
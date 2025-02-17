from django.shortcuts import render
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import SocialMediaAccount
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
    try:
        cart_data = json.loads(request.POST.get('cart_data', '[]'))
        print(cart_data)
        # Here you would typically:
        # 1. Validate the cart data
        # 2. Create an order in your database
        # 3. Process payment
        # 4. Update stock levels
        # 5. Send order confirmation email
        # For demo purposes, just return success
        return JsonResponse({
            'status': 'success',
            'message': 'Order processed successfully',
            'order_id': 'ORD-2024-001'  # Demo order ID
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
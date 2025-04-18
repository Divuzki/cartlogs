from decimal import Decimal
import random
import json
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect, reverse
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from .utils import ProcessKorapayPayment, caluate_gateway_fee
import requests
from django.views.decorators.csrf import csrf_exempt
from core.models import Wallet, Transaction
from marketplace.models import Order
import hmac
import hashlib
from django.utils.encoding import force_bytes
from django.db.models import Sum
import logging
import uuid
from django.core.mail import EmailMessage

logger = logging.getLogger(__name__)

def manual_payment(request, reference):

    # get transaction
    try:
        transaction = Transaction.objects.get(payment_reference=reference)
        amount = transaction.amount

        return render(request, 'manual_payment.html', {
            'amount': amount,
        'reference': reference
        })
    except Transaction.DoesNotExist:
        return JsonResponse({
          'success': False,
            'errors': {'general': 'Transaction not found'}
        })
    

def initiate_manual_payment(request, amount_in_kobo):
    amount_in_naira = Decimal(amount_in_kobo / 100)
    reference = str(uuid.uuid4().hex[:8])

    if amount_in_naira < Decimal('1000'):
        return JsonResponse({
            'success': False,
            'errors': {'amount': 'Minimum amount is ₦1,000'}
        })

    try:
        # Create a pending transaction
        transaction = Transaction.objects.create(
            wallet=request.user.wallet,
            amount=amount_in_naira,
            type='credit',
            description="Pending Manual Transfer",
            payment_reference=reference,
            payment_gateway='manual',
            status='pending'
        )
        transaction.save()

        # Cache the transaction reference for validation
        cache_key = f'manual_payment_{reference}'
        cache.set(cache_key, request.user.id, timeout=3600)  # 1 hour expiry

        # return render(request, 'manual_payment.html', {
        #     'amount': amount_in_naira,
        #     'reference': reference
        # })
        return JsonResponse({
                    'success': True,
                    'redirect_url': reverse('manual_payment', kwargs={'reference': reference})
                })

    except Exception as e:
        print(e)
        logger.error(f'Error initiating manual payment: {str(e)}')
        return JsonResponse({
            'success': False,
            'errors': {'general': 'An error occurred while initializing manual payment. Please try again.'}
        })

@require_http_methods(["POST"])
def confirm_manual_payment(request):
    try:
        data = json.loads(request.body)
        reference = data.get('reference')

        if not reference:
            return JsonResponse({
                'success': False,
                'error': 'Transaction reference is required'
            })

        # Validate transaction reference from cache
        cache_key = f'manual_payment_{reference}'
        cached_user_id = cache.get(cache_key)

        if not cached_user_id or cached_user_id != request.user.id:
            return JsonResponse({
                'success': False,
                'error': 'Invalid or expired transaction reference'
            })

        try:
            transaction = Transaction.objects.get(
                payment_reference=reference,
                wallet__user=request.user,
                status='pending'
            )
        except Transaction.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Transaction not found or already processed'
            })

        try:
            # Send email notification with improved error handling
            email = EmailMessage(
                'New Manual Payment Confirmation',
                f'A new manual payment has been confirmed:\n\n'
                f'Reference: {reference}\n'
                f'Amount: ₦{transaction.amount}\n'
                f'User: {request.user.email}\n'
                f'Time: {transaction.created_at}\n\n'
                f'Please verify the payment and mark it as successful in the admin panel.',
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL]
            )
            email.send(fail_silently=True)

            # Clear the cache after successful processing
            cache.delete(cache_key)

            return JsonResponse({
                'success': True,
                'redirect_url': '/add-funds/'
            })
        except Exception as e:
            logger.error(f'Error sending confirmation email: {str(e)}')
            # Still return success even if email fails
            return JsonResponse({
                'success': True,
                'redirect_url': '/add-funds/'
            })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid request format'
        })
    except Exception as e:
        logger.error(f'Error confirming manual payment: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while confirming payment. Please try again.'
        })

    except Exception as e:
        logger.error(e)
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while confirming payment'
        })


@ensure_csrf_cookie
def auth_page(request):
    """Render the authentication page"""
    if request.user.is_authenticated:
        return redirect('/')

    # check if reset=success is in the url
    param = request.GET.get('reset')
    next = request.GET.get('next')
    if not next:
        next = '/'
        
    return render(request, 'auth/auth.html', {'param': param, 'next': next})

@require_http_methods(["POST"])
def login_view(request):
    """Handle login form submission"""
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')

    username = username.lower().strip()
    
    if not username or not password:
        return JsonResponse({
            'success': False,
            'errors': {'general': 'Please provide both username and password'}
        })

    # check if username is email and check if email exists
    user_qs = User.objects.filter(email=username)
    if user_qs.exists():
        username = user_qs.first().username
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        login(request, user)
        return JsonResponse({
            'success': True,
            'redirect_url': '/'
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': {'general': 'Invalid credentials'}
        })

def logout_view(request):
    """Handle logout"""
    if request.user.is_authenticated:
        logout(request)
    return redirect('auth_page')

@require_http_methods(["POST"])
def signup_view(request):
    """Handle signup form submission"""
    data = json.loads(request.body)
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    password2 = data.get('password2')
    
    errors = {}

    username = username.lower().strip()
    email = email.lower().strip()
    
    # Validate input
    if not username:
        errors['username'] = 'Username is required'
    elif User.objects.filter(username=username).exists():
        errors['username'] = 'Username already exists'
        
    if not email:
        errors['email'] = 'Email is required'
    elif User.objects.filter(email=email).exists():
        errors['email'] = 'Email already exists'
        
    if not password:
        errors['password'] = 'Password is required'
    elif len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters'
        
    if password != password2:
        errors['password2'] = 'Passwords do not match'
        
    if errors:
        return JsonResponse({
            'success': False,
            'errors': errors
        })
    
    # Create user
    try:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        login(request, user)
        return JsonResponse({
            'success': True,
            'redirect_url': '/'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': {'general': 'An error occurred during registration'}
        })

def forget_passwords(request):
    return render(request, 'auth/forget_passwords.html')

@require_http_methods(["POST"])
def request_otp(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')

        if not email:
            return JsonResponse({'success': False, 'errors': {'email': 'Email is required'}})

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'errors': {'email': 'No account found with this email'}})

        # Generate 6-digit OTP
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Store OTP in cache with 10-minute expiry
        cache_key = f'password_reset_otp_{email}'
        cache.set(cache_key, otp, 600)  # 600 seconds = 10 minutes

        # Send OTP email
        send_mail(
            'Password Reset OTP',
            f'Your OTP for password reset is: {otp}\nThis OTP will expire in 10 minutes.',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'errors': {'general': str(e)}})

@require_http_methods(["POST"])
def reset_password(request):
    try:
        data = json.loads(request.body)
        email = data.get('email')
        otp = data.get('otp')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        # Validate input
        errors = {}
        if not email:
            errors['email'] = 'Email is required'
        if not otp:
            errors['otp'] = 'OTP is required'
        if not new_password:
            errors['new_password'] = 'New password is required'
        if not confirm_password:
            errors['confirm_password'] = 'Confirm password is required'
        if new_password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match'
        if len(new_password) < 8:
            errors['new_password'] = 'Password must be at least 8 characters long'

        if errors:
            return JsonResponse({'success': False, 'errors': errors})

        # Verify OTP
        cache_key = f'password_reset_otp_{email}'
        stored_otp = cache.get(cache_key)
        
        if not stored_otp or stored_otp != otp:
            return JsonResponse({'success': False, 'errors': {'otp': 'Invalid or expired OTP'}})

        # Update password
        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)
            user.save()

            # Delete OTP from cache
            cache.delete(cache_key)

            return JsonResponse({'success': True, 'redirect_url': '/auth'})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'errors': {'email': 'User not found'}})

    except Exception as e:
        return JsonResponse({'success': False, 'errors': {'general': str(e)}})

@login_required
@require_http_methods(["POST", "GET"])
def change_password(request):
    try:
        if request.method == 'GET':
            return render(request, 'auth/change_password.html')
        
        data = json.loads(request.body)
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validate current password
        if not request.user.check_password(current_password):
            return JsonResponse({
                'success': False,
                'errors': {'current_password': 'Current password is incorrect'}
            })
        
        # Validate password match
        if new_password != confirm_password:
            return JsonResponse({
                'success': False,
                'errors': {'confirm_password': 'Passwords do not match'}
            })
        
        # Update password
        request.user.set_password(new_password)
        request.user.save()
        
        # Update session to prevent logout
        update_session_auth_hash(request, request.user)
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': {'general': 'An error occurred while changing password'}
        })

@login_required
@require_http_methods(["GET"])
def profile(request):
    total_spent = Transaction.objects.filter(wallet=request.user.wallet, status='success').aggregate(Sum('amount'))['amount__sum'] or 0
    # add comma
    total_spent = format(total_spent, ',')
    return render(request, 'profile.html', {'total_spent': total_spent})

@require_http_methods(["GET"])
def disclaimer(request):
    return render(request, 'disclaimer.html')

KORAPAY_SECRET_KEY: str = settings.KORAPAY_SECRET_KEY

PAYMENT_GATEWAYS = settings.PAYMENT_GATEWAYS

@login_required
def add_funds(request):
    try:
        transactions = Transaction.objects.filter(
            wallet=request.user.wallet
        ).order_by('-created_at')
    except Wallet.DoesNotExist:
        # create wallet
        wallet = Wallet.objects.create(user=request.user)
        transactions = Transaction.objects.filter(
            wallet=wallet
        ).order_by('-created_at')
    return render(request, 'add_funds.html', {'transactions': transactions})

@login_required
@require_http_methods(["POST", "GET"])
def initiate_payment(request):

    if request.method == 'GET':
        trxref = request.GET.get('trxref')
        if not trxref:
            return redirect('add_funds')
        
        try:
            transaction = Transaction.objects.get(payment_reference=trxref)
            # check if the transaction is linked to a order
            if Order.objects.filter(transaction=transaction).exists():
                return redirect('marketplace:after_checkout', order_id=transaction.order.id)
            return redirect('add_funds')
        except Transaction.DoesNotExist:
            return redirect('add_funds')

    try:
        if request.user.wallet:
            pass
    except Wallet.DoesNotExist:
        # create wallet
        Wallet.objects.create(user=request.user)
        
    try:
        data = json.loads(request.body)
        amount = float(data.get('amount', 0))
        gateway = data.get('gateway')

        if gateway not in PAYMENT_GATEWAYS:
            return JsonResponse({
                'success': False,
                'errors': {'gateway': 'Invalid payment gateway selected'}
            })
            
        gateway_config = PAYMENT_GATEWAYS[gateway]
        if amount < gateway_config['min_amount'] or amount > gateway_config['max_amount']:
            return JsonResponse({
                'success': False,
                'errors': {'amount': f'Amount must be between ₦{gateway_config["min_amount"]:,.2f} and ₦{gateway_config["max_amount"]:,.2f}'}
            })

        # Convert amount to kobo/cents as required by payment gateways
        amount_in_kobo = int(amount * 100)

        if gateway == 'korapay':
            return initiate_korapay_payment(request, amount_in_kobo)
        elif gateway == 'manual':
            return initiate_manual_payment(request, amount_in_kobo)
            
    except Exception as e:
        logger.error(e)
        print(e)
        return JsonResponse({
            'success': False,
            'errors': {'general': 'An error occurred while processing payment'}
        })

def initiate_korapay_payment(request, amount_in_kobo):
    amount_in_naira = Decimal(amount_in_kobo / 100)
    # get next url
    next_url = request.GET.get('next')
    if not next_url:
        next_url = request.path

    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {settings.KORAPAY_SECRET_KEY}',
        }

        site_url = request.build_absolute_uri('/')

        # fee = caluate_gateway_fee(amount_in_naira)

        call_back_url = f'{site_url}{next_url}'

        # avoid double // between url and next_url without affect https://
        call_back_url = call_back_url.replace('//', '/').replace("https:/", "https://").replace("http:/", "http://")

        data = {
            'reference': str(uuid.uuid4().hex[:8]),
            'amount': (amount_in_kobo / 100),
            'redirect_url': call_back_url,
            'currency': 'NGN',
            'customer': {
                'email': request.user.email,
                'name': request.user.username,
            }
        }
        
        response = requests.post(
            f'https://api.korapay.com/merchant/api/v1/charges/initialize',
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            response_data = response.json()
            if response_data and response_data['data'] and response_data['data']['checkout_url']:
                transaction = Transaction.objects.create(wallet=request.user.wallet, amount=amount_in_naira, type='credit', 
                description="Pending Credit", payment_reference=data.get('reference'), payment_gateway='korapay')
                transaction.save()
                return JsonResponse({
                    'success': True,
                    'redirect_url': response_data['data']['checkout_url']
                })
        else:
            return JsonResponse({
                'success': False,
                'errors': {'general': 'Failed to initialize payment'}
            })
            
    except Exception as e:
        logger.error(e)
        return JsonResponse({
            'success': False,
            'errors': {'general': 'An error occurred while initializing payment'}
        })

@csrf_exempt
def korapay_webhook(request):
    HTTP_X_KORAPAY_SIGNATURE_EXIST = (
        "HTTP_X_KORAPAY_SIGNATURE" in request.META
        or "HTTP_X_KORAPAY_SIGNATURE_HEADER" in request.META
    )

    # update HTTP_X_KORAPAY_SIGNATURE_HEADER in request.META
    if "HTTP_X_KORAPAY_SIGNATURE_HEADER" in request.META:
        request.META["HTTP_X_KORAPAY_SIGNATURE"] = request.META[
            "HTTP_X_KORAPAY_SIGNATURE_HEADER"
        ]

    if request.method == "POST" and HTTP_X_KORAPAY_SIGNATURE_EXIST:
        # Get the Paystack signature from the headers
        paystack_signature = request.META["HTTP_X_KORAPAY_SIGNATURE"]
        # Get the request body as bytes
        raw_body = request.body
        decoded_body = raw_body.decode("utf-8")

        # Calculate the HMAC using the secret key
        calculated_signature = hmac.new(
            key=force_bytes(KORAPAY_SECRET_KEY),
            msg=force_bytes(decoded_body),
            digestmod=hashlib.sha512,
        ).hexdigest()

        # Compare the calculated signature with the provided signature
        # byepass signature verification for local development
        if (
            hmac.compare_digest(calculated_signature, paystack_signature)
            or settings.DEBUG
        ):
            # Signature is valid, proceed with processing the event
            try:
                # get the event from request.body
                event = json.loads(raw_body)
                # get the event type from event
                event_type = event["event"]
                # get the event data from event
                event_data = event["data"]
                # process_payment
                process_payment = ProcessKorapayPayment(event_type, event_data)
                return process_payment.process_payment()

            except UnicodeDecodeError:
                return HttpResponse("Invalid request body encoding", status=400)

        else:
            return HttpResponse("NOT ALLOWED", status=403)

    return HttpResponse("Invalid request", status=400)


@csrf_exempt
def etegram_webhook(request):
    print(request)
    if request.method != 'POST':
        return HttpResponse(status=405)
    
  
    
    # Process the webhook
    # try:
    payload = json.loads(request.body)
    _type = payload['type'] if payload['type'] else payload['data']['type']
    status = payload['status'] if payload['status'] else payload['data']['status']
    if _type == 'credit' and status == 'successful':
        try:
            # Get transaction reference
            reference = payload['reference'] if payload['reference'] else payload['data']['reference']
            
            # Get transaction
            transaction = Transaction.objects.get(payment_reference=reference)
            
            # Get wallet and credit it
            wallet = transaction.wallet
            wallet.credit(transaction.amount, transaction)
            wallet.save()
            
            return HttpResponse(status=200)
        except Transaction.DoesNotExist:
            return HttpResponse('Transaction not found', status=404)
        except Exception as e:
            logger.error(f'Error processing Etegram webhook: {str(e)}')
            return HttpResponse('Error processing payment', status=500)
    
    return HttpResponse(status=200)
    # except json.JSONDecodeError:
    #     return HttpResponse('Invalid JSON', status=400)
    # except KeyError:
    #     return HttpResponse('Invalid payload structure', status=400)

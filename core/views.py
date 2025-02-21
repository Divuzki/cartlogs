import random
import json
from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.core.cache import cache

@ensure_csrf_cookie
def auth_page(request):
    """Render the authentication page"""
    if request.user.is_authenticated:
        return redirect('/')

    # check if reset=success is in the url
    param = request.GET.get('reset')
    return render(request, 'auth/auth.html', {'param': param})

@require_http_methods(["POST"])
def login_view(request):
    """Handle login form submission"""
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return JsonResponse({
            'success': False,
            'errors': {'general': 'Please provide both username and password'}
        })
    
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

@require_http_methods(["POST"])
def signup_view(request):
    """Handle signup form submission"""
    data = json.loads(request.body)
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    password2 = data.get('password2')
    
    errors = {}
    
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
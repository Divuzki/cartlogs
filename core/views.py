from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
import json

@ensure_csrf_cookie
def auth_page(request):
    """Render the authentication page"""
    if request.user.is_authenticated:
        return redirect('/')
    return render(request, 'auth/auth.html')

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
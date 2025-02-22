from django.contrib import admin
from django.urls import path, include
from core.views import (auth_page, login_view, signup_view, request_otp, reset_password, forget_passwords, change_password, disclaimer, logout_view, orders, profile, add_funds)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('marketplace.urls', namespace='marketplace')),


    path('disclaimer/', disclaimer, name='disclaimer'),

    path('auth/', auth_page, name='auth_page'),
    path('auth/login/', login_view, name='login'),
    path('auth/signup/', signup_view, name='signup'),
    path('auth/request-otp/', request_otp, name='request_otp'),
    path('auth/reset-password/', reset_password, name='reset_password'),
    path('auth/forget-passwords/', forget_passwords, name='forget_passwords'),
    path('auth/change-password/', change_password, name='change_password'),
    
    path('auth/logout/', logout_view, name='logout'),

    path('orders/', orders, name='orders'),
    path('profile/', profile, name='profile'),
    path('add-funds/', add_funds, name='add_funds'),

]

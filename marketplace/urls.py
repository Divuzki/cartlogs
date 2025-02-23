# urls.py
from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.marketplace, name='home'),
    path('checkout/', views.checkout, name='checkout'),
    path('after_checkout/<int:order_id>/', views.after_checkout, name='after_checkout'),
    path('view_all/<str:social_media>/', views.view_all, name='view_all'),

    path('password_confirm/<str:order_number>/', views.password_confirm, name='password_confirm'),
    path('confirm/payment/', views.confirm_payment, name='confirm_payment'),
    path('cancel/<str:order_number>/', views.cancel_order, name='cancel_order'),
    path('orders/', views.orders, name='orders'),
    path('order_details/<int:order_id>/', views.order_details, name='order_details'),
]
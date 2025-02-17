# urls.py
from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.marketplace, name='home'),
    path('checkout/', views.checkout, name='checkout'),
]
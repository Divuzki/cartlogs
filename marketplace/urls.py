# urls.py
from django.urls import path
from . import views

app_name = 'marketplace'

urlpatterns = [
    path('', views.marketplace, name='home'),
    path('checkout/', views.checkout, name='checkout'),
    path('after_checkout/<int:order_id>/', views.after_checkout, name='after_checkout'),
    path('view_all/<str:social_media>/', views.view_all, name='view_all')
]
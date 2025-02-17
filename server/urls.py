from django.contrib import admin
from django.urls import path, include
from core.views import auth_page, login_view, signup_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('marketplace.urls', namespace='marketplace')),


    path('auth/', auth_page, name='auth_page'),
    path('auth/login/', login_view, name='login'),
    path('auth/signup/', signup_view, name='signup'),

]

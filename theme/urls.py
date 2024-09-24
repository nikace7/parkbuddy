from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='homepage'),
    path('save-parking-place/', views.save_parking_place , name='save_parking_place'),
    path('signup/', views.signup_view, name='signup'),
    path('login-otp/', views.login_with_otp_view, name='login_with_otp'),
    path('resend-otp/', views.resend_otp_view, name='resend_otp'),
]

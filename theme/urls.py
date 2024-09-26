from django.contrib import admin
from django.urls import path, include
from .views import *

urlpatterns = [
    path('', index, name='homepage'),
    path('save-parking-place/', save_parking_place , name='save_parking_place'),
    path('login/', login_view, name='login'),
    path('login-otp/', login_otp_view, name='login_otp'),
    path('delete-parking-place/<int:parking_place_id>/', delete_parking_place, name='delete_parking_place'),
]

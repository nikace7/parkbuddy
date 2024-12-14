from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('', index, name='homepage'),
    path('add-parking-place/', add_parking_place_view, name='add_parking_place'),
    path('save-parking-place/', save_parking_space, name='save_parking_space'),
    path('search-nearest-parking/', search_nearest_parking_spaces, name='search_nearest_parking'),
    path('login/', login_view, name='login'),
    path('login-otp/<str:phone_number>/', login_otp_view, name='login_otp'),
    path('logout', logout_api, name='logout'),
    path('book/<int:id>/', book_slot_view, name='book_slot'),
    path('book/<int:id>/payment', payment_view, name='book_slot_payment'),
    path('confirmation/<int:id>/', confirmation_view, name='confirmation'),
    path("", dashboard_view, name="dashboard"),
]

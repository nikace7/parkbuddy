from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='homepage'),
    path('save-parking-place/', views.save_parking_place , name='save_parking_place'),
]

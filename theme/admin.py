from django.contrib import admin
from .models import ParkingPlace

@admin.register(ParkingPlace)
class ParkingPlaceAdmin(admin.ModelAdmin):
    list_display = ('id', 'latitude', 'longitude', 'address', 'city', 'country')
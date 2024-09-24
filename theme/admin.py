from django.contrib import admin
from .models import ParkingPlace

@admin.register(ParkingPlace)
class ParkingPlaceAdmin(admin.ModelAdmin):
    list_display = ('latitude', 'longitude')

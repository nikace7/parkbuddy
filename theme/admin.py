from django.contrib import admin
from .models import  ParkingSpace

class ParkingSpaceAdmin(admin.ModelAdmin):
    list_display = ('name','vehicle_type', 'location', 'available')
    list_filter = ('vehicle_type', 'available')  # Filter by vehicle type or availability
    search_fields = ('vehicle_type',)  # Allow searching by vehicle type

# Register the models with the admin site
admin.site.register(ParkingSpace, ParkingSpaceAdmin)

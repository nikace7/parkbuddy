from django.contrib import admin
from .models import  ParkingSpace, UserProfile, ParkingSlot

class ParkingSpaceAdmin(admin.ModelAdmin):
    list_display = ('name','vehicle_type', 'location', 'available')
    list_filter = ('vehicle_type', 'available')  # Filter by vehicle type or availability
    search_fields = ('vehicle_type',)  # Allow searching by vehicle type

# Register the models with the admin site
admin.site.register(ParkingSpace, ParkingSpaceAdmin)

class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_parking_manager',)

admin.site.register(UserProfile, UserProfileAdmin)


admin.site.register(ParkingSlot)
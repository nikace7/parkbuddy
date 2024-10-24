from django.db import models
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models import PointField
from django.contrib.gis.db.models.functions import Distance
from django.contrib.auth import get_user_model

User = get_user_model()

# User model to register users with phone numbers
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, unique=True)  # Nepal country code + phone
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.phone_number

class Vehicle(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    vehicle_type = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=20)

#Parking Space model to store parking locations

class ParkingSpace(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    location = PointField(geography=True, srid=4326)
    available = models.BooleanField(default=True)
    vehicle_type = models.CharField(max_length=10, choices=[('Car', 'Car'), ('Bike', 'Bike')])

    def __str__(self):
        return f"{self.name}({self.vehicle_type} Parking at {self.location})"
    
class ParkingSlot(models.Model):
    parking_space = models.ForeignKey(ParkingSpace, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    booked_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.parking_space.name} - {self.user.username} - {self.booked_at}"
    
class ParkingBooking(models.Model):
    space = models.ForeignKey(ParkingSpace, on_delete=models.CASCADE)
    slot = models.ForeignKey(ParkingSlot, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)

    arriving_at = models.DateTimeField()
    exiting_at = models.DateTimeField()
    
    is_paid = models.BooleanField(default=False)    

class Payment(models.Model):
    slot = models.OneToOneField(ParkingSlot, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.slot} - {self.amount} - {self.paid_at}"    

# Function to find nearest parking spaces
def find_nearest_parking_spaces(user_latitude, user_longitude, max_distance_km=2, vehicle_type=None):
    user_location = Point(user_longitude, user_latitude, srid=4326)  # Longitude, Latitude order
    query = ParkingSpace.objects.filter(available=True)

    # Filter by vehicle type if provided
    if vehicle_type:
        query = query.filter(vehicle_type=vehicle_type)

    # Calculate distance and filter within the max distance
    nearest_parking_spaces = query.annotate(
        distance=Distance('location', user_location)
    ).order_by('distance').filter(distance__lt=max_distance_km * 1000)  # Convert km to meters

    return nearest_parking_spaces

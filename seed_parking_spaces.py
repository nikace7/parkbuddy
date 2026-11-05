import os

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'parkbuddy.settings')
django.setup()

from theme.models import ParkingSpace
from django.contrib.auth import get_user_model

User = get_user_model()

# Create a parking manager

User.objects.get_or_create(username='9876543210')

# Create 20 parking spaces for the parking manager

ParkingSpace.objects.get_or_create(
    user=User.objects.get(username='9876543210'),
    name='Parking Space 1',
    # Same (latitude, longitude) order as save_parking_space, and where the map opens.
    location='SRID=4326;POINT(27.7172 85.3240)',
    vehicle_type='Car',
    location_name='New Road',
    image1 = '',
    image2 = '',
    image3 = '',
    price_per_hr=50,
    price_per_half_hr=30,
    info='This is a parking space on New Road',
)
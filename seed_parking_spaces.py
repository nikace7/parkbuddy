from parkbuddy.theme.models import ParkingSpace
from django.contrib.auth import get_user_model

User = get_user_model()

# Create a parking manager

User.objects.create(
    username='9876543210',

)

# Create 20 parking spaces for the parking manager

ParkingSpace.objects.create(
    user=User.objects.get(username='9876543210'),
    name='Parking Space 1',
    location='SRID=4326;POINT(77.5946 12.9716)',
    vehicle_type='Car',
    location_name='MG Road',
    image1 = '',
    image2 = '',
    image3 = '',
    price_per_hr=50,
    price_per_half_hr=30,
    info='This is a parking space on MG Road',
)
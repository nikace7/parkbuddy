from django.db import models
from django.dispatch import receiver
from django.db.models.signals import pre_save
import requests  

class ParkingPlace(models.Model):
    latitude = models.FloatField()
    longitude = models.FloatField()
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f'{self.latitude}, {self.longitude} - {self.address}'

def fetch_location_data(latitude, longitude):
    api_url = f"https://geocode.maps.co/reverse?lat={latitude}&lon={longitude}"
    try:
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed with status code {response.status_code}")
    except Exception as e:
        print(f"Error occurred: {e}")
    return None


# Static method to handle pre-save signals
@receiver(pre_save, sender=ParkingPlace)
def populate_location_details(sender, instance, **kwargs):
    if not instance.address or not instance.city or not instance.country:
        data = fetch_location_data(instance.latitude, instance.longitude)
        if data and "address" in data:
            address_data = data['address']
            instance.address = address_data.get('suburb', '') or \
                               address_data.get('neighbourhood', '') or \
                               address_data.get('city_district', '')
            instance.city = address_data.get('city', '')
            instance.country = address_data.get('country', '')

        if not instance.address or not instance.city or not instance.country:
            print(f"Failed to fetch location data for ({instance.latitude}, {instance.longitude})")

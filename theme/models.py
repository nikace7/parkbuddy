from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import pre_save
import random , requests , json


class CustomUserManager(BaseUserManager):
    def create_user(self, phone_number, password=None):
        if not phone_number:
            raise ValueError("The Phone Number field must be set")
        user = self.model(phone_number=phone_number)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None):
        user = self.create_user(phone_number=phone_number, password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user

class CustomUser(AbstractBaseUser):
    phone_number = models.CharField(max_length=15, unique=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'phone_number'
    
    objects = CustomUserManager()

    def __str__(self):
        return self.phone_number

class OTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        self.otp_code = f'{random.randint(100000, 999999)}'  # 6-digit random OTP
        super().save(*args, **kwargs)

    def is_valid(self):
        now = timezone.now()
        # OTP is valid for 5 minutes
        return now <= self.created_at + timezone.timedelta(minutes=5)

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

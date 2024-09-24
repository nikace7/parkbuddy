from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone
import random

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
    
    def __str__(self):
        return f'{self.latitude}, {self.longitude}'
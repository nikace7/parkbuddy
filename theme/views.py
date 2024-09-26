from django.http import JsonResponse
from django.shortcuts import render , redirect
from .models import  ParkingPlace 
from django.contrib.auth import get_user_model
from django.contrib import messages
import random
import json


def index(request):
   return render(request, 'index.html')

def save_parking_place(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')

            # Create and save the ParkingPlace
            parking_place = ParkingPlace.objects.create(latitude=latitude, longitude=longitude)
            
            return JsonResponse({
                'status': 'success',
                'parking_place_id': parking_place.id,
                'address': parking_place.address,
                'city': parking_place.city,
                'country': parking_place.country,
            })
        except Exception as e:
            return JsonResponse({'status': 'failed', 'message': f'An error occurred: {e}'})
    return JsonResponse({'status': 'failed', 'message': 'Invalid request method.'})


def send_otp(phone_number, otp):
    # You can integrate an actual SMS service here to send the OTP
    print(f"OTP {otp} sent to {phone_number}")

def login_view(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone')

        if phone_number and len(phone_number) == 10:
            otp = random.randint(100000, 999999)  # Generate a 6-digit OTP
            request.session['phone_number'] = phone_number
            request.session['otp'] = otp
            send_otp(phone_number, otp)  # Mock sending OTP

            return redirect('login_otp')  # Redirect to OTP input page
        else:
            messages.error(request, "Please enter a valid 10-digit phone number.")

    return render(request, 'login.html')
def login_otp_view(request):
    phone_number = request.session.get('phone_number')
    
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        session_otp = request.session.get('otp')

        if otp_input and otp_input == str(session_otp):
            # OTP is correct, login the user
            # Here, you would log in or create the user based on phone number
            # For example: User.objects.get_or_create(phone_number=phone_number)
            messages.success(request, "Login successful!")
            return redirect('homepage')  # Redirect to homepage
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'login_otp.html', {'phone_number': phone_number})
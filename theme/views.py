from django.http import JsonResponse , HttpResponse
from django.shortcuts import render , redirect
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from .models import CustomUser, OTP , ParkingPlace 
from django.contrib.auth import get_user_model
from django.contrib import messages
from .forms import PhoneLoginForm, OTPVerificationForm
import random
from twilio.rest import Client
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



User = get_user_model()

# Function to simulate sending OTP (Replace with actual OTP service)
def send_otp(phone_number):
    otp = random.randint(100000, 999999)
    # Store OTP in session for demo (use cache/DB in production)
    return otp

# View for login with phone number
def login_view(request):
    if request.method == 'POST':
        form = PhoneLoginForm(request.POST)
        if form.is_valid():
            phone = form.cleaned_data['phone']
            otp = send_otp(phone)  # Simulate sending OTP
            request.session['otp'] = otp
            request.session['phone'] = phone
            return redirect('login_otp')  # Redirect to OTP page
    else:
        form = PhoneLoginForm()
    
    return render(request, 'login.html', {'form': form})

# View for OTP verification
def login_otp_view(request):
    phone = request.session.get('phone')
    
    if not phone:
        return redirect('login')  # Redirect to login if no phone session

    if request.method == 'POST':
        form = OTPVerificationForm(request.POST)
        if form.is_valid():
            input_otp = form.cleaned_data['otp']
            session_otp = request.session.get('otp')
            
            if input_otp == str(session_otp):
                # Successful login, create or retrieve user
                user, created = User.objects.get_or_create(phone=phone)
                # Log the user in (implement your own login logic)
                return redirect('homepage')  # Redirect to homepage after login
            else:
                messages.error(request, 'Invalid OTP, please try again.')
    else:
        form = OTPVerificationForm()

    return render(request, 'login_otp.html', {'form': form, 'phone_number': phone})

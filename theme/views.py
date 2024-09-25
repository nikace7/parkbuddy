from django.http import JsonResponse
from django.shortcuts import redirect, render 
from django.core.exceptions import ObjectDoesNotExist
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from .models import CustomUser, OTP , ParkingPlace 
from twilio.rest import Client
import json


def index(request):
   return render(request, 'index.html')


def login(request):
    if request.method == 'POST':
        # TODO: Phone number check and OTP send
        return render(request, 'login_otp.html', { 'phone_number': request.POST.get('phone') })
    
    return render(request, 'login.html')


def otp_check(request):
    if request.method == 'POST':
        # TODO: Check OTP and login the user
        return redirect('homepage')


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


# Twilio configuration (replace with your Twilio credentials)
TWILIO_ACCOUNT_SID = 'AC6ca22d0f756e6f6a6f63a9b13dd7adeb'
TWILIO_AUTH_TOKEN = '7e8a5074acb49df9900bf6ae893c4d67'
TWILIO_PHONE_NUMBER = '+9779861139971'

@csrf_exempt
def send_otp_via_sms(phone_number, otp_code):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = client.messages.create(
        body=f'Your OTP code is {otp_code}',
        from_=TWILIO_PHONE_NUMBER,
        to=phone_number
    )
    return message.sid

# Signup with OTP
@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')

            # Ensure the user exists, or create a new one
            user, created = CustomUser.objects.get_or_create(phone_number=phone_number)

            # Generate OTP (this is handled in the model save method)
            otp = OTP.objects.create(user=user)

            # Send OTP via SMS
            send_otp_via_sms(phone_number, otp.otp_code)

            return JsonResponse({'status': 'success', 'message': 'OTP sent successfully.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})


# Login with OTP Verification
@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        phone_number = data.get('phone_number')
        otp = data.get('otp')

        try:
            otp_verification = OTP.objects.get(phone_number=phone_number, otp=otp)
            if otp_verification.is_verified:
                return JsonResponse({'status': 'error', 'message': 'OTP already used.'})

            otp_verification.is_verified = True
            otp_verification.save()

            # Generate token or session (implement your token mechanism here)
            return JsonResponse({'status': 'success', 'message': 'Login successful.'})
        except ObjectDoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid OTP.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

@csrf_exempt
def resend_otp_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        phone_number = data.get('phone_number')

        try:
            user = CustomUser.objects.get(phone_number=phone_number)
            otp = OTP.objects.create(user=user)
            
            # Resend OTP via SMS
            send_otp_via_sms(phone_number, otp.otp_code)
            return JsonResponse({'status': 'success', 'message': 'OTP resent to your phone'})
        
        except CustomUser.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)


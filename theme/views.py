from django.http import JsonResponse
from django.shortcuts import render ,  redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import check_password
from .models import ParkingPlace
from django.views.decorators.csrf import csrf_exempt
from .models import CustomUser, OTP
from twilio.rest import Client
import json


def index(request):
   return render(request, 'index.html')

@csrf_exempt
def save_parking_place(request):
    if request.method == 'POST':    
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')

      
        parking_place = ParkingPlace.objects.create(latitude=latitude, longitude=longitude)
        
    
        return JsonResponse({'status': 'success', 'parking_spot_id': parking_place.id})
    
    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'})

# # Twilio configuration (replace with your Twilio credentials)
# TWILIO_ACCOUNT_SID = 'your_account_sid'
# TWILIO_AUTH_TOKEN = 'your_auth_token'
# TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'

# def send_otp_via_sms(phone_number, otp_code):
#     client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
#     message = client.messages.create(
#         body=f'Your OTP code is {otp_code}',
#         from_=TWILIO_PHONE_NUMBER,
#         to=phone_number
#     )
#     return message.sid

# def signup_view(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         phone_number = data.get('phone_number')
#         password = data.get('password')
        
#         if CustomUser.objects.filter(phone_number=phone_number).exists():
#             return JsonResponse({'status': 'error', 'message': 'Phone number already registered'}, status=400)
        
#         user = CustomUser.objects.create_user(phone_number=phone_number, password=password)
#         otp = OTP.objects.create(user=user)
        
#         # Send OTP via SMS
#         send_otp_via_sms(phone_number, otp.otp_code)
        
#         return JsonResponse({'status': 'success', 'message': 'OTP sent to your phone'})
#     return render(request, 'signup.html')

# def login_with_otp_view(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         phone_number = data.get('phone_number')
#         otp_code = data.get('otp')

#         try:
#             user = CustomUser.objects.get(phone_number=phone_number)
#             otp = OTP.objects.filter(user=user).last()
            
#             if otp and otp.is_valid() and otp.otp_code == otp_code:
#                 login(request, user)
#                 return JsonResponse({'status': 'success', 'message': 'Logged in successfully'})
#             else:
#                 return JsonResponse({'status': 'error', 'message': 'Invalid or expired OTP'}, status=400)
        
#         except CustomUser.DoesNotExist:
#             return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
    
#     return render(request, 'login_with_otp.html')

# def resend_otp_view(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         phone_number = data.get('phone_number')

#         try:
#             user = CustomUser.objects.get(phone_number=phone_number)
#             otp = OTP.objects.create(user=user)
            
#             # Resend OTP via SMS
#             send_otp_via_sms(phone_number, otp.otp_code)
#             return JsonResponse({'status': 'success', 'message': 'OTP resent to your phone'})
        
#         except CustomUser.DoesNotExist:
#             return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)


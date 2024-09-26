from django.http import JsonResponse
from django.shortcuts import render , redirect
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import  ParkingPlace 
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

@csrf_exempt
def delete_parking_place(request, parking_place_id):
    if request.method == 'DELETE': 
        try:
            parking_place = ParkingPlace.objects.get(id=parking_place_id)
            parking_place.delete()
            return JsonResponse({'status': 'success'}, status=200)
        except ParkingPlace.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Parking place not found'}, status=404)
    else:
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
    
def login_view(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone')

        if phone_number and len(phone_number) == 10:
            otp = random.randint(100000, 999999) 
            request.session['phone_number'] = phone_number
            request.session['otp'] = otp
            send_otp(phone_number, otp)  

            return redirect('login_otp')  
        else:
            messages.error(request, "Please enter a valid 10-digit phone number.")

    return render(request, 'login.html')
def login_otp_view(request):
    phone_number = request.session.get('phone_number')
    
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        session_otp = request.session.get('otp')

        if otp_input and otp_input == str(session_otp):
            messages.success(request, "Login successful!")
            return redirect('homepage')  
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'login_otp.html', {'phone_number': phone_number})
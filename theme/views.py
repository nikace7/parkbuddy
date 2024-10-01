from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.http import HttpResponse
from .models import ParkingSpace, find_nearest_parking_spaces, UserProfile
from django.contrib.gis.geos import Point
import json, random
import requests 

def index(request):
    return render(request, 'index.html')

def add_parking_place_view(request):
    return render(request, 'add_parking_place.html')

# Function to handle geocoding of location names using Nominatim
def geocode_location(location_name):
    """Geocode a location name to get latitude and longitude using Nominatim."""
    try:
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': location_name, 'format': 'json', 'limit': 1},
            headers={'User-Agent': 'ParkBuddyApp/1.0 (your_email@example.com)'}
        )

        if response.status_code == 200:
            data = response.json()
            if data:
                return float(data[0]['lat']), float(data[0]['lon'])
            else:
                print(f"Geocoding API returned no data for location: {location_name}")
        else:
            print(f"Geocoding API error: HTTP {response.status_code}")
    except Exception as e:
        print(f"Geocoding error: {e}")
    
    return None, None

# View to save parking space
@csrf_exempt
def save_parking_space(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        vehicle_type = data.get('vehicle_type')

        try:
            latitude = float(latitude)
            longitude = float(longitude)

            if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
                return JsonResponse({'status': 'error', 'message': 'Invalid latitude or longitude values.'})

            location = Point(longitude, latitude, srid=4326)  # Longitude first
            parking_space = ParkingSpace.objects.create(location=location, vehicle_type=vehicle_type)
            return JsonResponse({'status': 'success', 'message': 'Parking space saved!', 'id': parking_space.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Failed to save parking space: {e}'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

# View to find nearest parking spaces using KNN
def search_nearest_parking_spaces(request):
    if request.method == 'GET':
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        location_name = request.GET.get('search_term')
        vehicle_type = request.GET.get('vehicle_type', '')

        if latitude and longitude:
            try:
                latitude = float(latitude)
                longitude = float(longitude)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Invalid latitude or longitude values.'})
        elif location_name:
            latitude, longitude = geocode_location(location_name)
            if latitude is None or longitude is None:
                return JsonResponse({'status': 'error', 'message': 'Failed to retrieve location coordinates. Please try again with a valid location.'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Please provide a location name or valid coordinates.'})

        max_distance_km = 1

        try:
            nearest_spaces = find_nearest_parking_spaces(latitude, longitude, max_distance_km, vehicle_type=vehicle_type)

            response = [{
                'id': space.id,
                'vehicle_type': space.vehicle_type,
                'distance': round(space.distance.m, 2),
                'latitude': space.location.y,
                'longitude': space.location.x
            } for space in nearest_spaces]

            return JsonResponse({'status': 'success', 'data': response})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Failed to find parking spaces: {e}'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

# Function to send OTP using Sparrow SMS API
@csrf_exempt
def send_otp(phone_number, otp):
    sparrow_sms_url = "https://api.sparrowsms.com/v2/sms/"
    params = {
        'token': 'your_api_token',
        'from': 'ParkBuddy',
        'to': phone_number,
        'text': f"Your OTP is {otp}.",
    }
    response = requests.get(sparrow_sms_url, params=params)
    print(f"OTP {otp} sent to {phone_number} via Sparrow SMS")

@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        phone_number = request.POST.get('phone').strip()

        if len(phone_number) != 10 or not phone_number.isdigit():
            messages.error(request, 'Please enter a valid 10-digit phone number.')
            return render(request, 'login.html')

        try:
            user_profile = UserProfile.objects.get(phone_number=phone_number)
            return redirect('login_otp', phone_number=phone_number)
        except ObjectDoesNotExist:
            user = User.objects.create(username=phone_number)
            user.save()
            UserProfile.objects.create(user=user, phone_number=phone_number)

            otp = random.randint(100000, 999999)  # Generate a random 6-digit OTP
            send_otp(phone_number, otp)  # Send the OTP
            return redirect('login_otp', phone_number=phone_number)

    return render(request, 'login.html')
@csrf_exempt
def login_otp_view(request, phone_number):  # Accept phone_number as an argument
    if request.method == 'POST':
        otp = request.POST.get('otp')
        # Here you would validate the OTP with the Sparrow SMS API
        # Assuming OTP verification logic is in place
        user_profile = UserProfile.objects.get(phone_number=phone_number)
        login(request, user_profile.user)
        return redirect('homepage')

    return render(request, 'login_otp.html', {'phone_number': phone_number})
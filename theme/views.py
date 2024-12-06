from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.db.models import Count, Q
from .models import ParkingSpace, ParkingSlot, find_nearest_parking_spaces, UserProfile
from django.contrib.gis.geos import Point
from django.core.serializers import (
    serialize,
)
import json, random
import requests 
from django.contrib.auth import logout
from django.core import serializers

def index(request):
    parking_spaces = ParkingSpace.objects.all()
    parking_spaces_ctx = []
    for space in parking_spaces:
        parking_spaces_ctx.append({
            'id': space.id,
            'latitude': space.location[0],
            'longitude': space.location[1],
            'name': space.name,
            'vehicle_type': space.vehicle_type,
            'location_name': space.location_name,
            'available': space.available,
            'phone': space.user.username,
            'available_slots_count': space.parkingslot_set.filter(is_booked=False).count(),
            'price_per_hr': space.price_per_hr,
            'price_per_half_hr': space.price_per_half_hr,
            'image1': space.image1.url,
            'image2': space.image2.url,
            'image3': space.image3.url,
        })

    return render(request, 'index.html', {'parking_spaces': json.dumps(parking_spaces_ctx)})

def add_parking_place_view(request):
    if request.user.id == None or not request.user.profile.is_parking_manager:
        return redirect('homepage')
    
    return render(request, 'add_parking_place.html')

# Function to handle geocoding of location names using Nominatim
def geocode_location(location_name):
    """Geocode a location name to get latitude and longitude using Nominatim."""
    try:
        response = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': location_name, 'format': 'json', 'limit': 1},
            # headers={'User-Agent': 'ParkBuddyApp/1.0 (https://www.parkbuddy.com)'}
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
        name = request.POST.get('parking_name')
        vehicle_type = request.POST.get('vehicle_type')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')
        slots_count = request.POST.get('slots_count')
        price_per_hr = request.POST.get('price_per_hr')
        price_per_half_hr = request.POST.get('price_per_half_hr')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        image3 = request.FILES.get('image3')
        info = request.POST.get('info')

        location_name = ''

        res = requests.get(
                f"https://geocode.maps.co/reverse?api_key=65a96648e1cd3020225512hcq628bd0&lon={longitude}&lat={latitude}"
            )
        response = json.loads(res.text)

        if "suburb" in response["address"]:
            location_name = response["address"]["suburb"]
        elif "neighbourhood" in response["address"]:
            location_name = response["address"]["neighbourhood"]
        else:
            location_name = response["address"]["city_district"]

        parking_space = ParkingSpace.objects.create(
            name=name,
            location=Point(float(latitude), float(longitude)),
            vehicle_type=vehicle_type,
            location_name=location_name,
            user=request.user,
            price_per_hr=price_per_hr,
            price_per_half_hr=price_per_half_hr,
            image1 = image1,
            image2 = image2,
            image3 = image3,
            info = info,
        )
        parking_space.save()

        for i in range(int(slots_count)):
            ParkingSlot.objects.create(
                parking_space=parking_space,
                slot_number=i+1
            )

        add_another_vehicle_type = request.POST.get('action') == 'another_vehicle_type'

        if add_another_vehicle_type:
            vehicle_type = 'Car' if vehicle_type == 'Bike' else 'Bike'
            return render(request, 'add_parking_place.html', {'location_name': name, 'latitude': latitude, 'longitude': longitude, 'vehicle_type': vehicle_type})
        else:
            messages.info(request, 'Parking space added successfully.')
            return redirect('homepage')
        

# View to find nearest parking spaces using KNN
def search_nearest_parking_spaces(request):
    if request.method == 'GET':
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        location_name = request.GET.get('search_term ', 'Kathmandu')  # Default to Kathmandu
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
                'name': space.name,
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
        phone_number = request.POST.get('phone')
        otp = request.POST.get('otp')

        # Check if a user with this phone number exists
        try:
            user = User.objects.get(username=phone_number)
        except User.DoesNotExist:
            # If the user does not exist, create a new user
            user = User.objects.create(username=phone_number)
            profile = UserProfile.objects.create(user=user)
            user.save()
            profile.save()

        if otp != None:
            # Check if the OTP is correct
            if int(otp) == request.session['otp']:
                login(request, user)
                return redirect('homepage')
            else:
                messages.error(request, 'Invalid OTP. Please try again.')
                return redirect('login_otp', phone_number=phone_number)

        # Generate an OTP
        otp = random.randint(100000, 999999)

        # Store the OTP in session
        request.session['otp'] = otp
        request.session['phone_number'] = phone_number

        # Send the OTP to the user's phone number
        send_otp(phone_number, otp)

        # Redirect to the OTP verification view
        return redirect('login_otp', phone_number=phone_number)  # Change from render to redirect

    # If the request is GET, render the login page
    return render(request, 'login.html')


def logout_api(request):
    logout(request)
    return redirect('homepage')


@csrf_exempt
def login_otp_view(request, phone_number):  # Accept phone_number as an argument
    if request.method == 'POST':
        otp = request.POST.get('otp')
        # Here you would validate the OTP with the Sparrow SMS API
        # Assuming OTP verification logic is in placePlay 
        user = User.objects.get(username=phone_number)
        login(request, user)
        return redirect('homepage')

    return render(request, 'login_otp.html', {'phone_number': phone_number})

@csrf_exempt
def dashboard_view(request):
    parking_places = ParkingSpace.objects.annotate(
        num_available_slots=Count(
            "parkingslot", filter=~Q(parkingslot__is_booked=True)
        )
    )

    context = {}
    context["markers"] = json.loads(
        serialize(
            "geojson",
            parking_places,
        )
    )

    place_slots_count = {}
    for place in parking_places:
        place_slots_count[place.id] = place.num_available_slots
    context["place_slots_count"] = json.dumps(place_slots_count)

    return render(request, "index.html", context)


def book_slot_view(request, id):
    return render(request, 'book_slot.html')


def payment_view(request):
    return render(request, 'payment.html')


def confirmation_view(request):
    return render(request, 'confirmation.html')
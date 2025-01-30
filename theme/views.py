from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.contrib.auth import login
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.db.models import Count, Q
from .models import ParkingSpace, ParkingSlot, find_nearest_parking_spaces, UserProfile, ParkingBooking
from django.contrib.gis.geos import Point
from django.core.serializers import (
    serialize,
)
import json, random
import requests 
from django.contrib.auth import logout
from django.core import serializers
from datetime import datetime, timedelta
import pytz
import webbrowser
from chatbot_main.PABs import predict_class, get_response, intents

def index(request):
    parking_spaces = ParkingSpace.objects.all()
    parking_spaces_ctx = []
    for space in parking_spaces:
        available_slots_count = ParkingSlot.objects.filter(parking_space=space, is_disabled=False).count() - space.on_site_occupied_slots_count
        parking_spaces_ctx.append({
            'id': space.id,
            'latitude': space.location[0],
            'longitude': space.location[1],
            'name': space.name,
            'vehicle_type': space.vehicle_type,
            'location_name': space.location_name,
            'available': space.available,
            'phone': space.user.username,
            'available_slots_count': available_slots_count,
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
        'token': 'your_api_key',
        'from': 'PARKBUDDY',
        'to': phone_number,
        'text': f"Your OTP is {otp}.",
    }
    response = requests.get(sparrow_sms_url, params=params)
    print(response.text)
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
    if request.user.id == None:
        messages.info(request, 'Please login to book a parking slot.')
        return redirect('login')

    if request.method == 'POST':
        parking_space = ParkingSpace.objects.get(id=id)
        price = request.POST.get('price')
        date = request.POST.get('date')
        time = request.POST.get('time')
        vehicle_number = request.POST.get('vehicle_number')
        duration_hours = request.POST.get('duration_hours')
        duration_minutes = request.POST.get('duration_minutes')

        parking_slot = ParkingSlot.objects.filter(parking_space=parking_space, is_disabled=False).first()

        arriving_at = datetime.strptime(f'{date} {time}', '%Y-%m-%d %H:%M')
        exiting_at = arriving_at + timedelta(hours=int(duration_hours), minutes=int(duration_minutes))

        booking = ParkingBooking.objects.create(
            booked_by=request.user,
            space=parking_space,
            slot=parking_slot,
            vehicle_number=vehicle_number,
            arriving_at=arriving_at,
            exiting_at=exiting_at,
            price=price,
        )

        return redirect(
            'book_slot_payment',
            id=booking.id
        )
    else:
        parking_space = ParkingSpace.objects.get(id=id)
        if parking_space is None:
            return redirect('homepage')

        return render(request, 'book_slot.html', {'parking_space': parking_space})
    

def is_a_parking_slot_available(request):
    if request.method == 'GET':
        parking_space_id = request.GET.get('parking_space_id')
        arriving_date = request.GET.get('arriving_date')
        arriving_time = request.GET.get('arriving_time')
        parking_duration = request.GET.get('parking_duration')  # In number of seconds

        # The arriving_date will be in the format of '21/01/2025', arriving_time of '15:56' and parking_duration in the number of seconds. create a variable representing the python datetime data
        arriving_date = datetime.strptime(arriving_date, '%Y-%m-%d')
        arriving_time = datetime.strptime(arriving_time, '%H:%M')
        parking_duration = timedelta(seconds=int(parking_duration))
        arriving_time = arriving_date.replace(hour=arriving_time.hour, minute=arriving_time.minute).replace(tzinfo=pytz.UTC)

        parking_space = ParkingSpace.objects.get(id=parking_space_id)
        total_parking_slots = ParkingSlot.objects.filter(parking_space_id=parking_space_id, is_disabled=False).count() - parking_space.on_site_occupied_slots_count
        slots_booked = ParkingBooking.objects.filter(space_id=parking_space_id)
        for slot in slots_booked:
            if slot.arriving_at <= arriving_time and slot.exiting_at >= arriving_time:
                total_parking_slots = total_parking_slots - 1

        return JsonResponse({'available_slots': total_parking_slots})


def payment_view(request, id):
    parking_booking = ParkingBooking.objects.get(id=id)

    if request.method == 'POST':
        # Construct payload for Khalti
        # ----------------------------

        url = "https://a.khalti.com/api/v2/epayment/initiate/"

        payload = json.dumps(
            {
                "return_url": "http://127.0.0.1:8000/khalti/return",
                "website_url": "http://127.0.0.1:8000",
                "amount": str(parking_booking.price * 100),  # Khalti accepts amount in paisa
                "purchase_order_id": parking_booking.id,
                "purchase_order_name": "Park & Go",
                "customer_info": {
                    "name": request.user.username,
                },
            }
        )
        headers = {
            "Authorization": "key live_secret_key_68791341fdd94846a146f0457ff7b455",
            "Content-Type": "application/json",
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        return redirect(json.loads(response.text)["payment_url"])
    else:
        return render(request, 'payment.html', { 'price': parking_booking.price, 'id': id })


def confirmation_view(request, id):
    week_days = [
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
    ]

    parking_booking = ParkingBooking.objects.get(id=id)
    parking_space = ParkingSpace.objects.get(id=parking_booking.space.id)

    return render(request, 'confirmation.html', {
        'arriving_date': parking_booking.arriving_at.strftime('%d'),
        'arriving_month': parking_booking.arriving_at.strftime('%b'),
        'arriving_day': week_days[parking_booking.arriving_at.weekday()],
        'arriving_time': parking_booking.arriving_at.strftime('%I:%M %p'),
        'exiting_time': parking_booking.exiting_at.strftime('%I:%M %p'),
        'vehicle_type': parking_space.vehicle_type,
        'parking_name': parking_space.name,
        'location_name': parking_space.location_name,
        'is_paid': parking_booking.is_paid,
        'price': parking_booking.price,
    })



def view_bookings(request):
    all_bookings = ParkingBooking.objects.filter(booked_by=request.user)
    upcoming_bookings = []
    past_bookings = []

    for booking in all_bookings:
        if booking.arriving_at > datetime.now().replace(tzinfo=pytz.UTC):
            upcoming_bookings.append(booking)
        else:
            past_bookings.append(booking)

    return render(request, 'view_bookings.html', {'upcoming_bookings': upcoming_bookings, 'past_bookings': past_bookings})


def manage_parking_space(request):
    if request.user.id == None or not request.user.profile.is_parking_manager:
        return redirect('homepage')
    
    parking_spaces = ParkingSpace.objects.filter(user=request.user)

    print(parking_spaces)
    
    return render(request, 'manage_parking_space.html', { 'parking_spaces': parking_spaces })


def edit_parking_space_view(request, id):
    if request.user.id == None or not request.user.profile.is_parking_manager:
        return redirect('homepage')
    
    parking_space = ParkingSpace.objects.get(id=id)
    slots_count = ParkingSlot.objects.filter(parking_space=parking_space, is_disabled=False).count()

    return render(request, 'manage_parking_space_edit.html', { 'parking_space': parking_space, 'slots_count': slots_count })


def update_parking_space(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        name = request.POST.get('parking_name')
        vehicle_type = request.POST.get('vehicle_type')
        slots_count = request.POST.get('slots_count')
        on_site_occupied_count = request.POST.get('on_site_occupied_count')
        price_per_hr = request.POST.get('price_per_hr')
        price_per_half_hr = request.POST.get('price_per_half_hr')
        image1 = request.FILES.get('image1')
        image2 = request.FILES.get('image2')
        image3 = request.FILES.get('image3')
        info = request.POST.get('info')

        parking_space = ParkingSpace.objects.get(id=id)
        parking_space.name = name
        parking_space.vehicle_type = vehicle_type
        parking_space.price_per_hr = price_per_hr
        parking_space.price_per_half_hr = price_per_half_hr
        if image1 != None:
            parking_space.image1 = image1
        if image2 != None:
            parking_space.image2 = image2
        if image3 != None:
            parking_space.image3 = image3
        parking_space.info = info
        parking_space.on_site_occupied_slots_count = on_site_occupied_count

        parking_space.save()

        current_slots_count = ParkingSlot.objects.filter(parking_space=parking_space, is_disabled=False).count()
        if current_slots_count != int(slots_count):
            if current_slots_count > int(slots_count):
                slots_to_disable = current_slots_count - int(slots_count)
                for i in range(slots_to_disable):
                    slot = ParkingSlot.objects.filter(parking_space=parking_space, is_disabled=False).last()
                    slot.is_disabled = True
                    slot.save()
            else:
                for i in range(int(slots_count) - current_slots_count):
                    ParkingSlot.objects.create(
                        parking_space=parking_space,
                        slot_number=current_slots_count + i + 1
                    )

        messages.info(request, 'Parking space updated successfully.')
        return redirect(request.META.get('HTTP_REFERER'))


def khalti_return(request):
    if request.method == 'GET':
        parking_booking_id = request.GET.get('purchase_order_id')
        status = request.GET.get('status')

        if status == 'Completed':
            booking = ParkingBooking.objects.get(id=parking_booking_id)
            booking.is_paid = True
            booking.save()

            return redirect('confirmation', id=parking_booking_id)
        else:
            return HttpResponse('Payment failed. Please try again.')


def contains_link(response):
    # A simple check for 'http' or 'https' in the response
    if 'http' in response or 'https' in response:
        return True
    return False

def extract_link(response):
    # Extract the link from the response (assuming the link is enclosed in <>)
    start_index = response.find('<')
    end_index = response.find('>')
    if start_index != -1 and end_index != -1:
        return response[start_index + 1:end_index]
    return None

@csrf_exempt
def chatbot(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_input = data.get('message')
        predicted_intent = predict_class(user_input)
        response = get_response(predicted_intent, intents)
        if contains_link(response):
            link = extract_link(response)
            webbrowser.open(link)
        return JsonResponse({'response': response})
      
    return JsonResponse({'error': 'Invalid request method'}, status=400)




from .utils import knn_search

def search_nearest_parking_spaces(request):
    """
    API endpoint to search for the nearest parking spaces based on user's location.

    """
    try:
        user_lat = float(request.GET.get('latitude'))
        user_lon = float(request.GET.get('longitude'))
        vehicle_type = request.GET.get('vehicle_type')  # Optional filter

        # Get parking spaces from the database
        parking_spaces = ParkingSpace.objects.all()
        if vehicle_type:
            parking_spaces = parking_spaces.filter(vehicle_type=vehicle_type)

        # Find nearest parking spaces using KNN
        nearest_spaces = knn_search(parking_spaces, user_lat, user_lon, k=5)

        # Prepare response data
        data = [
            {
                "id": space.id,
                "name": space.name,
                "latitude": space.latitude,
                "longitude": space.longitude,
                "vehicle_type": space.vehicle_type,
                "distance": round(distance, 2),
                "available_slots": space.available_slots,
            }
            for space, distance in nearest_spaces
        ]

        return JsonResponse({"parking_spaces": data}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

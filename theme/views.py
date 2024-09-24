from django.http import JsonResponse
from django.shortcuts import render
from .models import ParkingPlace
from django.views.decorators.csrf import csrf_exempt
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
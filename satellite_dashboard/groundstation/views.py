from django.shortcuts import render
from django.http import JsonResponse
from .services.firebase_service import FirebaseService
import json

# Create Firebase service instance
firebase_service = FirebaseService()

def dashboard(request):
    """Main dashboard view"""
    return render(request, 'groundstation/dashboard.html')

def get_latest_data(request):
    """API endpoint to get latest sensor data"""
    data = firebase_service.get_latest_data()
    return JsonResponse(data if data else {})

def get_historical_data(request):
    """API endpoint to get historical sensor data for graphs"""
    # Get period from request, default to all available data
    limit = request.GET.get('limit', 50)
    try:
        limit = int(limit)
    except ValueError:
        limit = 50
    
    data = firebase_service.get_historical_data(limit=limit)
    return JsonResponse(data)

def send_command(request):
    """API endpoint to send commands to the satellite"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            command_type = data.get('type')
            command_value = data.get('value')
            
            success = firebase_service.send_command(command_type, command_value)
            
            return JsonResponse({'success': success})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

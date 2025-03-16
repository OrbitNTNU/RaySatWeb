from django.shortcuts import render
from django.http import JsonResponse
from groundstation.services.firebase_service import FirebaseService
import json

# Create Firebase service instance
firebase_service = FirebaseService()

def dashboard(request):
    """Main dashboard view"""
    return render(request, 'groundstation/dashboard.html')

# def get_latest_data(request):
#     """API endpoint to get latest sensor data"""
#     data = firebase_service.get_latest_data()
#     return JsonResponse(data if data else {})

def get_latest_data(request):
    data = firebase_service.get_latest_data()  # Fetch data from Firebase
    return JsonResponse(data if isinstance(data, dict) else data, safe=False)

def get_historical_data(request):
    """API endpoint to get historical sensor data for graphs"""
    # Get period from request, default to last 24 hours
    period = request.GET.get('period', '24h')
    
    # In a real implementation, you would filter data based on period
    data = firebase_service.get_all_data()
    
    # Process data for graphs
    processed_data = process_data_for_graphs(data)
    
    return JsonResponse(processed_data)

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

def process_data_for_graphs(data):
    """Helper function to format data for graphing"""
    # This will depend on your exact data structure
    # Here's a simplistic example
    result = {
        'timestamps': [],
        'inside_temperature': [],
        'outside_temperature': [],
        'pressure': [],
        'uv': [],
        'ozone': [],
        'gyro': {
            'x': [],
            'y': [],
            'z': []
        },
        'height': []
    }
    
    # Assuming data is a dict with timestamp keys
    for timestamp, reading in sorted(data.items()):
        result['timestamps'].append(timestamp)
        result['inside_temperature'].append(reading.get('insideTemp'))
        result['outside_temperature'].append(reading.get('outsideTemp'))
        result['pressure'].append(reading.get('pressure'))
        result['uv'].append(reading.get('uv'))
        result['ozone'].append(reading.get('ozone'))
        result['gyro']['x'].append(reading.get('gyroX'))
        result['gyro']['y'].append(reading.get('gyroY'))
        result['gyro']['z'].append(reading.get('gyroZ'))
        result['height'].append(reading.get('height'))
    
    return result
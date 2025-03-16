from firebase_admin import db, credentials
import firebase_admin
import os
from dotenv import load_dotenv

class FirebaseService:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize Firebase connection
        self.database_url = os.getenv('databaseURL')
        cred = credentials.Certificate("credentials.json")
        
        try:
            firebase_admin.initialize_app(cred, {"databaseURL": self.database_url})
        except ValueError:
            # App already initialized
            pass
            
        self.root_ref = db.reference("/")
        
    def get_latest_data(self):
        """Fetch the latest sensor reading from Firebase"""
        # Get the 'Latest' node directly
        latest_data = self.root_ref.child('Latest').get()
        return latest_data
    
    def get_historical_data(self, limit=50):
        """Fetch historical sensor data for graphs"""
        # Get data from 'sensordata' node, limited to the last 'limit' entries
        sensor_data = self.root_ref.child('sensordata').order_by_key().limit_to_last(limit).get()
        
        # Process the data into a format suitable for charts
        processed_data = self._process_sensor_data(sensor_data)
        return processed_data
    
    def _process_sensor_data(self, sensor_data):
        """Process the raw sensor data into a format suitable for charts"""
        if not sensor_data:
            return {
                'timestamps': [],
                'inside_temperature': [],
                'outside_temperature': [],
                'pressure': [],
                'uv': [],
                'ozone': [],
                'gyro': {'x': [], 'y': [], 'z': []}
            }
        
        # Initialize result dictionary
        result = {
            'timestamps': [],
            'inside_temperature': [],
            'outside_temperature': [],
            'pressure': [],
            'uv': [],
            'ozone': [],
            'gyro': {'x': [], 'y': [], 'z': []}
        }
        
        # Sort data by timestamp (which is the key)
        sorted_data = sorted(sensor_data.items(), key=lambda x: int(x[0]))
        
        # Process each reading
        for timestamp_str, reading in sorted_data:
            result['timestamps'].append(int(timestamp_str))
            result['inside_temperature'].append(reading.get('insideTemp'))
            result['outside_temperature'].append(reading.get('outsideTemp'))
            result['pressure'].append(reading.get('pressure'))
            result['uv'].append(reading.get('uv', 0))
            result['ozone'].append(reading.get('ozone'))
            result['gyro']['x'].append(reading.get('gyroX'))
            result['gyro']['y'].append(reading.get('gyroY'))
            result['gyro']['z'].append(reading.get('gyroZ'))
        
        return result
    
    def send_command(self, command_type, command_value):
        """Send command to the satellite via Firebase"""
        commands_ref = self.root_ref.child('commands')
        import time
        timestamp = int(time.time() * 1000)
        
        new_command = {
            'type': command_type,
            'value': command_value,
            'timestamp': timestamp,
            'executed': False
        }
        
        commands_ref.push().set(new_command)
        return True

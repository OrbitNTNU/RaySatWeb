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
        """Fetch only the latest sensor reading"""
        return self.root_ref.child('latest').get()
    def get_sensor_data(self, period='24h'):
        """
        Fetch sensor data from Firebase for the specified period
        
        Args:
            period (str): Period to fetch data for ('24h', '7d', '30d', 'all')
            
        Returns:
            dict: Dictionary of timestamp-indexed sensor readings
        """
        # Get reference to the sensordata node
        sensor_ref = self.root_ref.child('sensordata')
        
        # Get all sensor data (we'll filter by time later if needed)
        sensor_data = sensor_ref.get()
        
        # If period is 'all' or we got no data, return whatever we have
        if not sensor_data or period == 'all':
            return sensor_data or {}
        
        # Filter data based on period
        # Calculate cutoff timestamp
        import time
        current_time_ms = int(time.time() * 1000)
        
        if period == '24h':
            cutoff_time_ms = current_time_ms - (24 * 60 * 60 * 1000)  # 24 hours in milliseconds
        elif period == '7d':
            cutoff_time_ms = current_time_ms - (7 * 24 * 60 * 60 * 1000)  # 7 days in milliseconds
        elif period == '30d':
            cutoff_time_ms = current_time_ms - (30 * 24 * 60 * 60 * 1000)  # 30 days in milliseconds
        else:
            return sensor_data  # Default to all data for unrecognized periods
        
        # Filter data by timestamp
        # Note: This assumes your timestamps are relative to current time, not from takeoff
        # If they're from takeoff, you'll need to adjust this logic
        filtered_data = {ts: data for ts, data in sensor_data.items() if int(ts) >= cutoff_time_ms}
        
        return filtered_data
    
    def process_data_for_graphs(data):
        """Helper function to format data for graphing"""
        # Initialize result structure
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
            'height': [],
            'wheel_speed': []  # Added for completeness, even if not in your data yet
        }
        
        if not data:
            return result
        
        # Sort timestamps to ensure chronological order
        sorted_timestamps = sorted(data.keys(), key=lambda x: int(x))
        
        # Extract data for each timestamp
        for timestamp in sorted_timestamps:
            reading = data[timestamp]
            
            # Add data points to respective arrays
            result['timestamps'].append(timestamp)
            
            # Use .get() with None default for potentially missing values
            result['inside_temperature'].append(reading.get('insideTemp'))
            result['outside_temperature'].append(reading.get('outsideTemp'))
            result['pressure'].append(reading.get('pressure'))
            result['uv'].append(reading.get('uv'))
            result['ozone'].append(reading.get('ozone'))
            result['gyro']['x'].append(reading.get('gyroX'))
            result['gyro']['y'].append(reading.get('gyroY'))
            result['gyro']['z'].append(reading.get('gyroZ'))
            result['height'].append(reading.get('height'))
            result['wheel_speed'].append(reading.get('wheelSpeed', None))
        
        return result

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
                'gyro': {'x': [], 'y': [], 'z': []},
                'height': []
            }
        
        # Initialize result dictionary
        result = {
            'timestamps': [],
            'inside_temperature': [],
            'outside_temperature': [],
            'pressure': [],
            'uv': [],
            'ozone': [],
            'gyro': {'x': [], 'y': [], 'z': []},
            'height': []
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
            result['height'].append(reading.get('height'))
        
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

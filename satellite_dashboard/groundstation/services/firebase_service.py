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
        
    def get_all_data(self):
        """Fetch all sensor data from Firebase"""
        return self.root_ref.get()
    
    def get_latest_data(self):
        """Fetch only the latest sensor reading"""
        # Assuming data is stored with timestamp as key
        # This might need adjustment based on your data structure
        data = self.root_ref.order_by_key().limit_to_last(1).get()
        return next(iter(data.values())) if data else None
    
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

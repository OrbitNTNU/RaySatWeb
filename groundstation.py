from firebase_admin import db, credentials
from dotenv import load_dotenv
import firebase_admin

import os
import serial

load_dotenv()

GCP_PROJECT_ID = os.getenv('projectID')
SERIVCE_ACCOUNT_ID = os.getenv('SERVICE_ACCOUNT_FILE')
STORAGE_BUCKET_NAME = os.getenv('storageBucket')
DATABASE_URL = os.getenv('databaseURL')

# default_app = firebase_admin.initialize_app()
cred = credentials.Certificate("credentials.json")
firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

ref = db.reference("/")
print(ref.get())


SERIAL_PORT = 'COM3' # COM3 if Windows, /dev/ttyUSB0 if Linux
BAUD_RATE = 38400


try:
    ser = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE)
except serial.SerialException as e:
    print(f"Error opening serial port {SERIAL_PORT}: {e}")
    exit()

"""
data in format:
timestamp_ms;pressure_hPa;insideTemperature_C;outsideTemperature_C;UV_candela;ozone_ppm;gyro_x;gyro_y;gyro_z
"""

def addToFirebase(line):
    data = line.split(";")
    if len(data) != 9:
        print("Invalid data format!")
        return
    
    timestamp, pressure, inside_temp, outside_temp, uv, ozone, gyro_x, gyro_y, gyro_z = data
    print(line)
    timestamp = line[0] # ms
    pressure = line[1]  # hPa
    insideTemp = line[2]    # degree C
    outsideTemp = line[3]   # degree C
    uv = line[4]    # candela
    ozone = line[5] # ppm
    gyroX = line[6]
    gyroY = line[7]
    gyroZ = line[8]

    data_entry = {
        'timestamp': timestamp,
        'pressure': pressure,
        'insideTemp': insideTemp,
        'outsideTemp': outsideTemp,
        'uv': uv,
        'ozone': ozone,
        'gyroX': gyroX,
        'gyroY': gyroY,
        'gyroZ': gyroZ
    }

    readings_ref = ref.child('sensordata')
    readings_ref.child(timestamp).set(data_entry)
    
    # Gets latest data
    ref.child('latest').set(data_entry)


while True:
    try:
        lineBinary = ser.readline()
        line = lineBinary.decode('ascii')
        line = line.replace("\n", "")
        print(line)

    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        ser.close()
        break


"""
ref = db.referenece('sensordata/temperature')

# Saving userinfo to database located at an URL server (in JSON)
# Alternative 1, overwrites data located at users_ref
users_ref = ref.child('users')          
users_ref.set({
    'john': {
        'date_of_birth': '14. september 1999'
        'full_name': 'John Paulson'
    },
    'paul': {
        'date_of_birth': '24. april 1970'
        'full_name': 'Paul John'
    }
    'joe': {
        'date_of_birth': '6. september 1879'
        'full_name': 'Joe'
    }
})

# Alternative 2, does not overwrite data but rather just modifies the child node bob
users_ref.child('bob').set({            
    'date_of_birth': '20. oktober 2025'
    'full_name': 'Bob Bobson'
}
)

# Updating saved data, set instead of update would delete the other data already known (date of birth and full name)
hopper_ref = users_ref.child('micho')
hopper_ref.update({
    'nickname': 'Amazing Mike'
})

# Can update multiple users/child-node at once
users_ref.update({
    'ablerto/nickname': 'Brilliant Albert',
    'micho/nickname': 'Amazing Mike'
})

# Overwrites the entire user when updating. Removes fex date of bith and full_name
users_ref.update({
    'ablerto': {
        'nickname': 'Brilliant Albert'
    },
    'micho': {
        'nickname': 'Amazing Mike'
    }
})
"""

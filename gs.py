import serial
import sys
import json
import os

from datetime import datetime
from firebase_admin import db, credentials
from dotenv import load_dotenv
import firebase_admin


import ngham

load_dotenv()

"""
data in format:
callsign;timestamp_ms;pressure_hPa;insideTemperature_C;outsideTemperature_C;UV_candela;ozone_ppm;height;rwoffon;rwmanual

(nvm no gyro)

test datastring:
"LA9ORB;104912;1000;23;24;0;30;100;on;off"

"""


GCP_PROJECT_ID = os.getenv('projectID')
SERIVCE_ACCOUNT_ID = os.getenv('SERVICE_ACCOUNT_FILE')
STORAGE_BUCKET_NAME = os.getenv('storageBucket')
DATABASE_URL = os.getenv('databaseURL')

# default_app = firebase_admin.initialize_app()
cred = credentials.Certificate("credentials.json")
firebase_admin.initialize_app(cred, {"databaseURL": DATABASE_URL})

ref = db.reference("/")
# print(ref.get())

SERIAL_PORT = 'COM3'  # COM3 if Windows, /dev/ttyUSB0 if Linux
BAUD_RATE = 38400
START_BYTE = ngham.START_BYTE


def read_exactly(ser, n):
    """Read exactly n bytes from serial."""
    data = b""
    while len(data) < n:
        chunk = ser.read(n - len(data))  # Read missing bytes
        if not chunk:
            return None  # Handle errors (timeout, disconnection)
        data += chunk
    return list(data)


try:
    ser = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE)
except serial.SerialException as e:
    print(f"Error opening serial port {SERIAL_PORT}: {e}")
    exit()

print(f"Listening on {SERIAL_PORT} at {BAUD_RATE} baud...")


def add_to_firebase(data_list):
    timestamp = int(data_list[0])  # ms
    pressure = float(data_list[1])  # hPa
    insideTemp = float(data_list[2])  # degree C
    outsideTemp = float(data_list[3])  # degree C
    uv = float(data_list[4])  # candela
    ozone = float(data_list[5])  # ppm
    height = float(data_list[6])
    rwstate = str(data_list[7])
    rwmanual = str(data_list[8])

    data_entry = {
        'timestamp': timestamp,
        'pressure': pressure,
        'insideTemp': insideTemp,
        'outsideTemp': outsideTemp,
        'uv': uv,
        'ozone': ozone,
        'height': height,
        'rwstate': rwstate,
        'rwmanual': rwmanual,
    }

    readings_ref = ref.child('sensordata')
    readings_ref.child(str(timestamp)).set(data_entry)
    
    # Gets latest data
    ref.child('latest').set(data_entry)



while True:
    try:
        data_b = ser.read()

        if not data_b:
            continue

        byte_value = data_b[0]

        if byte_value == START_BYTE:
            print("Found NGHam-SPP Frame Start")

            ngham_header = [byte_value]

            header_data = read_exactly(ser, 4)
            if header_data is None:
                print("Error: Incomplete NGHam-SPP Header")
                continue

            ngham_header.extend(header_data)

            _, _, _, pl_len = ngham.decode_ngham_spp_header_only(ngham_header)

            ngham_payload = read_exactly(ser, pl_len)
            if ngham_payload is None:
                print("Error: Incomplete NGHam-SPP Payload")
                continue

            ngham_spp_packet = ngham_header + ngham_payload
            ngham_spp_packet_decoded = ngham.decode_ngham_spp_packet(ngham_spp_packet)

            now = datetime.now()
            current_time = now.strftime("%Y_%m_%d_%H_%M_%S")
            print(current_time)

            readings_ref = ref.child('owldata')
            readings_ref.child(str(current_time)).set(ngham_spp_packet_decoded)
            
            print("Decoded NGHam-SPP Packet:")
            # print(json.dumps(ngham_spp_packet_decoded, indent=2))
            # print(json.dumps(ngham_spp_packet_decoded["spp_payload"]["data"], indent=2))
            # print(type(ngham_spp_packet_decoded["spp_payload"]["data"]))
            try:
                if ngham_spp_packet_decoded["spp_payload"]["data"]["ngham_flags"] == "0x0":
                    sensor_data = ngham_spp_packet_decoded["spp_payload"]["data"]["rx_payloads"].get("sensor_data")
                    if sensor_data:
                        print(sensor_data)
                        add_to_firebase(sensor_data)
            except:
                continue        

        else:
            print("No NGHam-SPP Frame Start")
            print("Data:", data_b.hex(), end=" ")
            sys.stdout.flush()

    except KeyboardInterrupt:
        print("continue")
import threading
import time
import json
import uuid
import geocoder
import asyncio
from queue import Queue
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, firestore
import mpu6050_sensor_data
import main_mlx90614
import main_max30102


# Function to get latitude and longitude using WiFi
def get_lat_long():
    # Using geocoder to get the current location based on WiFi/IP
    g = geocoder.ip('me')  # 'me' returns location based on current IP address
    return g.latlng  # Returns [latitude, longitude]


def collect_mpu6050_data(data_queue, stop_event):
    while not stop_event.is_set():
        mpu6050_data = mpu6050_sensor_data.collect_sensor_data()
        data_queue.put(mpu6050_data)  # Add data to the queue
        time.sleep(2)


def collect_accel_temp_hr_data(data_queue, stop_event):
    while not stop_event.is_set():
        accel_data = mpu6050_sensor_data.read_accelerometer_data()
        body_temp_data = main_mlx90614.get_object_temperature()
        heart_rate_data, spo2 = main_max30102.read_heart_rate()
        # Combine accel_data and body_temp_data into a tuple (or a dictionary if preferred)
        combined_data = (accel_data, body_temp_data, heart_rate_data, spo2)

        # Put the combined data in the queue
        data_queue.put(combined_data)
        time.sleep(2)


async def values(stop_event):
    mpu6050_data_queue = Queue()  
    accel_temp_hr_data_queue = Queue()

    mpu6050_data_thread = threading.Thread(target=collect_mpu6050_data, args=(mpu6050_data_queue, stop_event))
    mpu6050_data_thread.daemon = True  # Allows the program to exit even if the thread is running
    mpu6050_data_thread.start()

    accel_temp_hr_thread = threading.Thread(target=collect_accel_temp_hr_data, args=(accel_temp_hr_data_queue, stop_event))
    accel_temp_hr_thread.daemon = True  # Allows the program to exit even if the thread is running
    accel_temp_hr_thread.start()

    try:
        while not stop_event.is_set():
            # Handle accelerometer and gyroscope data
            if not mpu6050_data_queue.empty():
                mpu6050_thread_data = mpu6050_data_queue.get()
                print("Data from thread:", mpu6050_thread_data)

            # Handle accelerometer, temperature, and heart rate data
            if not accel_temp_hr_data_queue.empty():
                accel_temp_hr_thread_data = accel_temp_hr_data_queue.get()
                print("Data from thread:", accel_temp_hr_thread_data)

                data_for_firebase["body_temp"] = accel_temp_hr_thread_data[1]
                data_for_firebase["heart_rate"] = float(accel_temp_hr_thread_data[2])
                data_for_firebase["blood_oxygen"] = accel_temp_hr_thread_data[3]

                current_datetime = datetime.now(tz=timezone.utc)
                data_for_firebase["date_time"] = current_datetime
                data_for_firebase["address"] = "Koparkhairane, Navi Mumbai, Maharashtra, INDIA, 400709"
                data_for_firebase["description"] = "Autodetected by the device"
                data_for_firebase["id"] = str(reportID)

                if lat_lon:
                    latitude, longitude = lat_lon
                    data_for_firebase["location"] = firestore.GeoPoint(latitude, longitude)
                else:
                    data_for_firebase["location"] = None

                data_for_firebase["photo"] = []
                data_for_firebase["type_of_event"] = "Hardware Device"
                data_for_firebase["user_id"] = "VjoXUDwAI7Q0FxFoRdOmGagXOYk1"
                data_for_firebase["user_type"] = "Victim"
                data_for_firebase["video"] = []
                data_for_firebase["authority_id"] = None

                # json_data = json.dumps(data_for_firebase, indent=4)
                print(data_for_firebase)

                # Save to Firestore
                try:
                    # doc_ref = db.collection("reports").document(str(reportID))
                    # doc_ref.set(data_for_firebase)
                    print(f"Data successfully written to Firestore: {reportID}")
                except Exception as e:
                    print(f"Error writing to Firestore: {e}")

            time.sleep(5)

    except KeyboardInterrupt:
        print('Keyboard interrupt detected, exiting...')
        mpu6050_data_thread.join()
    finally:
        print('All threads stopped and completed.')

if __name__ == "__main__":
    data_for_firebase = {}

    # Generate a unique ID using uuid4
    reportID = uuid.uuid4()
    lat_lon = get_lat_long()

    # Initialize Firebase Admin SDK
    cred = credentials.Certificate('serviceAccountKey.json')  # Replace with your service account JSON file path
    firebase_admin.initialize_app(cred)

    # Initialize Firestore
    db = firestore.client()

    # Create stop event
    stop_event = threading.Event()

    try:
        asyncio.run(values(stop_event))
    except KeyboardInterrupt:
        print("Program interrupted. Stopping threads...")
        stop_event.set()
        print("Threads are gracefully stopped.")




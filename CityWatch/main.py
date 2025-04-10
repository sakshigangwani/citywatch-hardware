import sys
import threading
import time
import json
import uuid
import geocoder
import asyncio
import signal
import pickle
import numpy as np
from queue import Queue
from datetime import datetime, timezone
import firebase_admin
from firebase_admin import credentials, firestore
import mpu6050_sensor_data
import main_mlx90614
import main_max30102
import RPi.GPIO as GPIO


# Function to get latitude and longitude using WiFi
def get_lat_long():
    # Using geocoder to get the current location based on WiFi/IP
    g = geocoder.ip('me')  # 'me' returns location based on current IP address
    return g.latlng  # Returns [latitude, longitude]


def predict_fall_from_data(sensor_data):
    # Ensure correct feature order
    feature_order = [
        "acc_max",
        "acc_kurtosis",
        "acc_skewness",
        "gyro_kurtosis",
        "gyro_skewness",
        "lin_max",
        "post_lin_max",
        "post_gyro_max"
    ]

    # Extract values in correct order
    values = [sensor_data[feature] for feature in feature_order]  # shape: (8,)

    # Convert to 2D array for scaler and model: shape (1, 8)
    input_array = np.array([values])

    # Scale
    scaled_input = fall_detection_scaler.transform(input_array)

    # Predict
    prediction = fall_detection_model.predict(scaled_input)

    # Result
    result = "Fall Detected" if prediction[0] == 1 else "No Fall"

    return result


def predict_stress_from_data(sensor_data):
    accel, hr, temp, spo2 = sensor_data

    # Extract accel data
    x = accel["x"]
    y = accel["y"]
    z = accel["z"]

    # Get current time info
    now = datetime.now()
    month = now.month
    time_of_day = now.hour + now.minute / 60 + now.second / 3600

    # Arrange features in model's expected order
    features = [x, y, z, hr, temp, time_of_day, month]
    input_array = np.array([features])
    scaled_input = stress_detection_scaler.transform(input_array)

    # Predict
    prediction = stress_detection_model.predict(scaled_input)
    predicted_class = np.argmax(prediction[0])

    # Map to label
    stress_labels = {
        0: "No Stress",
        1: "Medium Stress",
        2: "High Stress"
    }

    return stress_labels.get(predicted_class, "Unknown")


def collect_mpu6050_data(data_queue):
    global stop_threads

    while not stop_threads:
        mpu6050_data = mpu6050_sensor_data.collect_sensor_data()

        result = predict_fall_from_data(mpu6050_data)

        print(f"\n[INFO] Result from predict_fall_from_data: {result}\n")

        data_queue.put(mpu6050_data)  # Add data to the queue
        time.sleep(2)


def collect_accel_temp_hr_data(data_queue):
    global stop_threads

    while not stop_threads:
        accel_data = mpu6050_sensor_data.read_accelerometer_data()
        body_temp_data = main_mlx90614.get_object_temperature()
        heart_rate_data, spo2 = main_max30102.read_heart_rate()
        # Combine accel_data and body_temp_data into a tuple (or a dictionary if preferred)
        combined_data = (accel_data, body_temp_data, heart_rate_data, spo2)

        result = predict_stress_from_data(combined_data)

        print(f"\n[INFO] Result from predict_stress_from_data: {result}\n")

        # Put the combined data in the queue
        data_queue.put(combined_data)
        time.sleep(2)


def send_to_firebase_on_button_press():
    global stop_threads, use_firebase, db

    try:
        while not stop_threads:
            time.sleep(0.2)
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                print("\n[INFO] Button is pressed\n")
                # Save to Firestore
                try:
                    # Generate a unique ID using uuid4
                    reportID = uuid.uuid4()
                    
                    data_for_firebase["id"] = str(reportID)

                    current_datetime = datetime.now(tz=timezone.utc)
                    data_for_firebase["date_time"] = current_datetime

                    print(f"\n[INFO] Data to be written to Firestore: \n{data_for_firebase}\n")

                    # Only write to Firestore if --firebase flag is set
                    if use_firebase:
                        doc_ref = db.collection("reports").document(str(reportID))
                        doc_ref.set(data_for_firebase)
                        print(f"[INFO] Data successfully written to Firestore: {reportID}\n")
                    else:
                        print("[INFO] Firestore write skipped (use --firebase to enable)\n")

                except Exception as e:
                    print(f"\n[ERROR] Error writing to Firestore: {e}\n")
            else:
                pass
    except KeyboardInterrupt:
        GPIO.cleanup()


async def values():
    global stop_threads

    mpu6050_data_queue = Queue()  
    accel_temp_hr_data_queue = Queue()

    mpu6050_data_thread = threading.Thread(target=collect_mpu6050_data, args=(mpu6050_data_queue,))
    mpu6050_data_thread.daemon = True  # Allows the program to exit even if the thread is running
    mpu6050_data_thread.start()

    accel_temp_hr_thread = threading.Thread(target=collect_accel_temp_hr_data, args=(accel_temp_hr_data_queue,))
    accel_temp_hr_thread.daemon = True  # Allows the program to exit even if the thread is running
    accel_temp_hr_thread.start()

    button_thread = threading.Thread(target=send_to_firebase_on_button_press)
    button_thread.daemon = True
    button_thread.start()

    try:
        while not stop_threads:
            # Handle accelerometer and gyroscope data
            if not mpu6050_data_queue.empty():
                mpu6050_thread_data = mpu6050_data_queue.get()
                print("\n[INFO] Data from mpu6050 thread:")
                print(json.dumps(mpu6050_thread_data, indent=4))
                print("\n")

            # Handle accelerometer, temperature, and heart rate data
            if not accel_temp_hr_data_queue.empty():
                accel_temp_hr_thread_data = accel_temp_hr_data_queue.get()
                print("\n[INFO] Data from accel temp hr thread:")
                print(json.dumps(accel_temp_hr_thread_data, indent=4))
                print("\n")

                data_for_firebase["body_temp"] = accel_temp_hr_thread_data[1]
                data_for_firebase["heart_rate"] = float(accel_temp_hr_thread_data[2])
                data_for_firebase["blood_oxygen"] = accel_temp_hr_thread_data[3]

                data_for_firebase["address"] = "SVKMs Dwarkadas J. Sanghvi College of Engineering, Vile Parle, Maharashtra, India, 400056"
                data_for_firebase["description"] = "Autodetected by the device"

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

            time.sleep(5)

    except Exception as e:
        print(f"\n[ERROR] An error occurred: {e}\n")
    finally:
        GPIO.cleanup()
        print("\n[INFO] Stopping all threads and exiting program.\n")


def signal_handler(sig, frame):
    global stop_threads

    print("\n[INFO] Ctrl + C detected. Stopping all threads...\n")
    stop_threads = True


if __name__ == "__main__":
    data_for_firebase = {}
    stop_threads = False

    # Check if "--firebase" is passed in the command line
    use_firebase = "--firebase" in sys.argv

    BUTTON_PIN = 16
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    lat_lon = get_lat_long()

    # 🔹 Initialize Firebase only if --firebase flag is set
    if use_firebase:
        cred = credentials.Certificate('serviceAccountKey.json')  # Replace with your service account JSON file path
        firebase_admin.initialize_app(cred)
        # Initialize Firestore
        db = firestore.client()
        print("\n[INFO] Firestore is enabled.\n")
    else:
        print("\n[INFO] Firestore is disabled. Use --firebase to enable it.\n")

    signal.signal(signal.SIGINT, signal_handler)

    # Load Fall Detection Model and Scaler
    with open('./ML_Models/Fall_Detection/fall_detection.pkl', 'rb') as f1:
        fall_detection_model = pickle.load(f1)

    with open('./ML_Models/Fall_Detection/scaler.pkl', 'rb') as f2:
        fall_detection_scaler = pickle.load(f2)

    # Load Fall Detection Model and Scaler
    with open('./ML_Models/Stress_Detection/stress_detection.pkl', 'rb') as f3:
        stress_detection_model = pickle.load(f3)

    with open('./ML_Models/Stress_Detection/stress_scaler.pkl', 'rb') as f4:
        stress_detection_scaler = pickle.load(f4)

    asyncio.run(values())

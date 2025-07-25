import mpu6050
import time
import numpy as np
from scipy.stats import kurtosis, skew

# Create a new Mpu6050 object
mpu6050 = mpu6050.mpu6050(0x68)

# Define a function to read the sensor data
def read_sensor_data():
    # Read the accelerometer values
    accelerometer_data = mpu6050.get_accel_data()

    # Read the gyroscope values
    gyroscope_data = mpu6050.get_gyro_data()

    # Read temp
    temperature = mpu6050.get_temp()

    return accelerometer_data, gyroscope_data, temperature

def read_accelerometer_data():
    return mpu6050.get_accel_data()

# Function to calculate acceleration magnitude
def calculate_magnitude(data):
    return np.sqrt(data['x']**2 + data['y']**2 + data['z']**2)

def collect_sensor_data(window_size=3):
    # Define lists to store data for window
    accel_data = []
    gyro_data = []

    # Collect data over time
    start_time = time.time()
    while True:
        accelerometer_data, gyroscope_data, temperature = read_sensor_data()
        
        # Append new data to the window
        accel_data.append(accelerometer_data)
        gyro_data.append(gyroscope_data)
        
        # Check if we have enough data for a full window
        if time.time() - start_time >= window_size:
            # Convert accelerometer data to magnitudes
            acc_magnitudes = [calculate_magnitude(acc) for acc in accel_data]
            gyro_magnitudes = [calculate_magnitude(gyro) for gyro in gyro_data]
            
            # Extract the data for the required time windows (4th and 6th seconds)
            acc_window_4th = acc_magnitudes[3] if len(acc_magnitudes) > 3 else None
            gyro_window_4th = gyro_magnitudes[3] if len(gyro_magnitudes) > 3 else None
            
            # Calculate max values for 4th second
            acc_max = np.max(acc_window_4th) if acc_window_4th else None

            # Calculate kurtosis and skewness for accelerometer and gyroscope
            acc_kurtosis_value = kurtosis(acc_magnitudes)
            gyro_kurtosis_value = kurtosis(gyro_magnitudes)
            
            acc_skewness_value = skew(acc_magnitudes)
            gyro_skewness_value = skew(gyro_magnitudes)
            
            # Calculate linear acceleration (assuming gravity is along the z-axis)
            lin_acc = np.array([acc['x'] for acc in accel_data])  # x-axis
            if len(lin_acc) > 3:
                lin_acc[3] = lin_acc[3] - 9.81  # Subtract gravity from 4th second data

            lin_max = np.max(lin_acc[5]) if len(lin_acc) > 5 else None  # 6th second maximum linear acceleration
            
            post_lin_max = np.max(lin_acc) if len(lin_acc) > 0 else None  # Max linear acceleration post-window
            
            post_gyro_max = np.max(gyro_magnitudes[5]) if len(gyro_magnitudes) > 5 else None  # 6th second max gyroscope magnitude
            
            # Return the results
            return {
                "acc_max": acc_max,
                "acc_kurtosis": acc_kurtosis_value,
                "acc_skewness": acc_skewness_value,
                "gyro_kurtosis": gyro_kurtosis_value,
                "gyro_skewness": gyro_skewness_value,
                "lin_max": lin_max,
                "post_lin_max": post_lin_max,
                "post_gyro_max": post_gyro_max
            }
        
        time.sleep(0.1)  # Sleep to prevent overloading CPU

# Example usage
if __name__ == "__main__":
    results = collect_sensor_data(window_size=3)
    print(results)

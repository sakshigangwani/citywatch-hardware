import max30102 
max30102_sensor = max30102.MAX30102()

def read_max30102_sensor_data():
    red, ir = max30102_sensor.read_sequential()
    print("red values:",red,"/n","ir values:",ir)
    return red, ir
    
if __name__ == "__main__":
    read_max30102_sensor_data()

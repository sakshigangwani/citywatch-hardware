from smbus2 import SMBus
from mlx90614 import MLX90614


def get_object_temperature():
    bus = SMBus(1)

    try:
        sensor = MLX90614(bus, address=0x5A)
        obj_temp = sensor.get_obj_temp()
        return obj_temp
    finally:
        bus.close()


def get_ambient_temperature():
    bus = SMBus(1)

    try:
        sensor = MLX90614(bus, address=0x5A)
        amb_temp = sensor.get_amb_temp()
        return amb_temp
    finally:
        bus.close()


if __name__ == "__main__":
    print("Object Temperature:", get_object_temperature(), "°C")
    print("Ambient Temperature:", get_ambient_temperature(), "°C")
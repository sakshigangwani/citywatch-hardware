import RPi.GPIO as GPIO
import time

BUTTON_PIN = 16
GPIO.setmode(GPIO.BCM)

GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

try:
    while True:
        time.sleep(0.1)
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            print("Button is pressed")
        else:
            # print("Button is not pressed")
            pass
except KeyboardInterrupt:
    GPIO.cleanup()
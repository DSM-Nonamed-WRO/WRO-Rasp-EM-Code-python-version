from HandsON_BuildHat_API import ColorSensor
import time

sensor = ColorSensor('C')

while True:
    value = sensor.get_reflected_light()
    print(value)
    time.sleep(0.1)
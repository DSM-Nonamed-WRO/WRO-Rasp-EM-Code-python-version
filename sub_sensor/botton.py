import time
from HandsON_BuildHat_API import BuildHat

hat = BuildHat()

while True:
    print(hat.stop_button.is_pressed())
    time.sleep(0.1)
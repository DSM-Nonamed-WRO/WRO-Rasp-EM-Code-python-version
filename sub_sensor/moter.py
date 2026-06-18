import time
from HandsON_BuildHat_API import Motor

motor = Motor('B')

print("start")
motor.start(50)
time.sleep(2)
motor.stop()
print("stop")
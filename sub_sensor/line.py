import time
from HandsON_BuildHat_API import BuildHat, MotorPair, ColorSensor

LEFT_PORT = 'A'
RIGHT_PORT = 'B'
COLOR_PORT = 'C'

BASE_SPEED = 30
MAX_SPEED = 55
MAX_CORRECTION = 12

KP = 0.18
KI = 0.0
KD = 0.03

TARGET = (34 + 98) / 2

hat = BuildHat()
drive = MotorPair(LEFT_PORT, RIGHT_PORT)
sensor = ColorSensor(COLOR_PORT)

integral = 0
last_error = 0
last_time = time.time()
stopped = False


def clamp(value, min_value=-MAX_SPEED, max_value=MAX_SPEED):
    return max(min_value, min(max_value, value))


def safe_stop():
    global stopped

    if stopped:
        return

    stopped = True
    print("Stopping motors...")

    drive.start_tank(0, 0)
    time.sleep(0.1)

    drive.stop()
    time.sleep(0.1)

    drive.start_tank(0, 0)
    print("Motor stopped")


try:
    print("Right line PID tracing start")

    while True:
        if hat.stop_button.is_pressed():
            print("STOP button pressed")
            safe_stop()
            break

        light = sensor.get_reflected_light()

        now = time.time()
        dt = now - last_time

        error = TARGET - light
        integral += error * dt
        derivative = (error - last_error) / dt if dt > 0 else 0

        correction = KP * error + KI * integral + KD * derivative
        correction = clamp(correction, -MAX_CORRECTION, MAX_CORRECTION)

        left_speed = BASE_SPEED - correction
        right_speed = BASE_SPEED + correction

        left_speed = clamp(left_speed)
        right_speed = clamp(right_speed)

        drive.start_tank(int(left_speed), int(right_speed))

        print(f"light={light}, L={left_speed:.1f}, R={right_speed:.1f}")

        last_error = error
        last_time = now

        time.sleep(0.01)

except KeyboardInterrupt:
    print("Keyboard stop")

finally:
    safe_stop()
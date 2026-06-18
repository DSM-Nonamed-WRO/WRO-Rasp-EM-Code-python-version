import time
import cv2
import numpy as np
from HandsON_BuildHat_API import MotorPair, DistanceSensor

LEFT_PORT = 'A'
RIGHT_PORT = 'B'
DISTANCE_PORT = 'D'

WIDTH = 320
HEIGHT = 240

BASE_SPEED = 28
MAX_SPEED = 45

TURN_GAIN = 0.12
MAX_CORRECTION = 10

TARGET_DISTANCE = 10
MIN_AREA = 500

SENSOR_OFFSET_PIXEL = 35

ROI_X_START = 0.0
ROI_X_END   = 1.0
ROI_Y_START = 0.35
ROI_Y_END   = 0.95

drive = MotorPair(LEFT_PORT, RIGHT_PORT)
distance_sensor = DistanceSensor(DISTANCE_PORT)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 30)

filtered_error = 0


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def safe_stop():
    drive.start_tank(0, 0)
    time.sleep(0.1)
    drive.stop()
    time.sleep(0.1)
    drive.start_tank(0, 0)


def get_distance():
    return distance_sensor.get_distance_cm()


def make_red_mask(hsv):
    lower_red1 = np.array([0, 120, 70])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([170, 120, 70])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

    return cv2.bitwise_or(mask1, mask2)


def get_roi_bounds():
    x1 = int(WIDTH * ROI_X_START)
    x2 = int(WIDTH * ROI_X_END)
    y1 = int(HEIGHT * ROI_Y_START)
    y2 = int(HEIGHT * ROI_Y_END)
    return x1, y1, x2, y2


def make_green_mask(hsv):
    lower_green = np.array([40, 81, 28])
    upper_green = np.array([108, 255, 212])

    return cv2.inRange(hsv, lower_green, upper_green)


def draw_roi(frame):
    x1, y1, x2, y2 = get_roi_bounds()
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)


def clean_mask(mask):
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def detect_object(frame, color_mode):
    x1, y1, x2, y2 = get_roi_bounds()
    roi = frame[y1:y2, x1:x2]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    if color_mode == "RED":
        mask = make_red_mask(hsv)
    else:
        mask = make_green_mask(hsv)

    mask = clean_mask(mask)

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return False, None, 0, mask, None

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)

    if area < MIN_AREA:
        return False, None, area, mask, None

    x, y, w, h = cv2.boundingRect(largest)

    x += x1
    y += y1
    cx = x + w // 2
    cy = y + h // 2

    return True, cx, area, mask, (x, y, w, h, cx, cy)


def choose_target(frame):
    red_found, red_cx, red_area, red_mask, red_box = detect_object(frame, "RED")
    green_found, green_cx, green_area, green_mask, green_box = detect_object(frame, "GREEN")

    if red_found and green_found:
        if red_area >= green_area:
            return "RED", red_cx, red_area, red_mask, red_box
        else:
            return "GREEN", green_cx, green_area, green_mask, green_box

    if red_found:
        return "RED", red_cx, red_area, red_mask, red_box

    if green_found:
        return "GREEN", green_cx, green_area, green_mask, green_box

    combined_mask = cv2.bitwise_or(red_mask, green_mask)
    return None, None, 0, combined_mask, None


def draw_box(frame, color_mode, box):
    if box is None:
        return

    x, y, w, h, cx, cy = box

    if color_mode == "RED":
        color = (0, 0, 255)
    else:
        color = (0, 255, 0)

    cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
    cv2.circle(frame, (cx, cy), 5, color, -1)
    cv2.putText(
        frame,
        color_mode,
        (x, y - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        color,
        2
    )


def avoid_right():
    print("Avoid right start")

    drive.start_tank(40, -40)
    time.sleep(0.55)

    drive.start_tank(40, 40)
    time.sleep(1)

    drive.start_tank(-35, 35)
    time.sleep(0.45)

    drive.start_tank(35, 35)
    time.sleep(1.8)

    safe_stop()
    print("Avoid right done")


def avoid_left():
    print("Avoid left start")

    drive.start_tank(-40, 40)
    time.sleep(0.35)

    drive.start_tank(40, 40)
    time.sleep(0.67)

    drive.start_tank(35, -35)
    time.sleep(0.6)

    drive.start_tank(35, 35)
    time.sleep(1.8)

    drive.start_tank(40, -40)
    time.sleep(0.35)

    drive.start_tank(35, 35)
    time.sleep(1.8)

    safe_stop()
    print("Avoid left done")


try:
    print("Auto color tracking start")
    print("카메라 창에서  's' = 시작 ,  'w' = 종료")

    # ===== 출발 대기 =====
    started = False
    while True:
        ret, frame = cap.read()

        if not ret:
            print("Camera read failed")
            break

        cv2.putText(
            frame,
            "s = START    w = QUIT",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )
        draw_roi(frame)
        cv2.imshow("Camera", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            started = True
            break
        elif key == ord('w'):
            break

    # ===== 실제 주행 (started 일 때만) =====
    while started:
        ret, frame = cap.read()

        if not ret:
            print("Camera read failed")
            break

        mode, cx, area, mask, box = choose_target(frame)

        camera_center_x = WIDTH // 2
        target_x = camera_center_x - SENSOR_OFFSET_PIXEL

        cv2.line(frame, (camera_center_x, 0), (camera_center_x, HEIGHT), (255, 0, 0), 2)
        cv2.line(frame, (target_x, 0), (target_x, HEIGHT), (0, 255, 255), 2)
        draw_roi(frame)

        if mode is not None:
            draw_box(frame, mode, box)

            distance = get_distance()
            error = cx - target_x

            filtered_error = filtered_error * 0.7 + error * 0.3

            print(
                f"mode={mode}, cx={cx}, target_x={target_x}, "
                f"error={error:.1f}, filtered={filtered_error:.1f}, "
                f"area={area}, distance={distance}"
            )

            if distance <= TARGET_DISTANCE:
                safe_stop()

                if mode == "RED":
                    avoid_right()

                elif mode == "GREEN":
                    avoid_left()

                filtered_error = 0
                time.sleep(0.5)
                continue

            correction = filtered_error * TURN_GAIN
            correction = clamp(correction, -MAX_CORRECTION, MAX_CORRECTION)

            left_speed = BASE_SPEED + correction
            right_speed = BASE_SPEED - correction

            left_speed = clamp(left_speed, -MAX_SPEED, MAX_SPEED)
            right_speed = clamp(right_speed, -MAX_SPEED, MAX_SPEED)

            drive.start_tank(int(left_speed), int(right_speed))

        else:
            print("No red or green object found")
            drive.start_tank(18, -18)

        cv2.imshow("Camera", frame)
        cv2.imshow("Mask", mask)

        if cv2.waitKey(1) & 0xFF == ord('w'):
            break

        time.sleep(0.03)

except KeyboardInterrupt:
    print("Keyboard stop")

finally:
    safe_stop()
    cap.release()
    cv2.destroyAllWindows()

import time
import cv2
import numpy as np
from HandsON_BuildHat_API import MotorPair, DistanceSensor

from ROI import WIDTH, HEIGHT, detect_object, detect_all_objects, draw_roi, get_roi_bounds
from devide import draw_divisions, get_weight

LEFT_PORT = 'A'
RIGHT_PORT = 'B'
DISTANCE_PORT = 'D'

BASE_SPEED = 28
MAX_SPEED = 45

TURN_GAIN = 0.12
MAX_CORRECTION = 10

TARGET_DISTANCE = 10

SENSOR_OFFSET_PIXEL = 35

# ===== 카메라만 테스트할 땐 False (모터/거리센서 사용 안 함) =====
USE_HARDWARE = False


class DummyDrive:
    # 하드웨어 없이 테스트할 때 모터 명령을 무시하는 가짜 드라이브
    def start_tank(self, left, right):
        pass

    def stop(self):
        pass


if USE_HARDWARE:
    drive = MotorPair(LEFT_PORT, RIGHT_PORT)
    distance_sensor = DistanceSensor(DISTANCE_PORT)
else:
    drive = DummyDrive()
    distance_sensor = None

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
    if distance_sensor is None:
        return 999  # 센서 없을 때는 항상 멀리 있다고 간주 (회피 동작 안 함)
    return distance_sensor.get_distance_cm()


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


def draw_detection_status(frame, mode, weight=None):
    # ROI 안에 빨강/초록이 들어왔을 때 화면 하단에 표시 (색 + 현재 가중치)
    if mode == "RED":
        text = "RED IN ROI"
        color = (0, 0, 255)
    elif mode == "GREEN":
        text = "GREEN IN ROI"
        color = (0, 255, 0)
    else:
        text = "NO TARGET"
        color = (200, 200, 200)

    if weight is not None:
        text += f"  W:{weight}"

    cv2.putText(
        frame,
        text,
        (10, HEIGHT - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        color,
        1
    )


def draw_labels(frame, objects):
    # 화면 전체의 빨강/초록 객체를 네모로 감싸고 "색 거리" 라벨을 붙인다.
    # 거리: 박스가 클수록(가까울수록) 1, 작을수록(멀수록) 2, 3 ...
    ordered = sorted(objects, key=lambda o: o["area"], reverse=True)

    for distance, obj in enumerate(ordered, start=1):
        color = (0, 0, 255) if obj["color"] == "RED" else (0, 255, 0)

        x, y, w, h = obj["x"], obj["y"], obj["w"], obj["h"]
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        label = f"{obj['color']} {distance}"
        cv2.putText(
            frame,
            label,
            (x, y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            color,
            1
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
            "s = START   w = QUIT",
            (5, 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (0, 255, 255),
            1
        )
        draw_roi(frame)
        rx1, ry1, rx2, ry2 = get_roi_bounds()
        draw_divisions(frame, rx1, ry1, rx2, ry2)
        draw_labels(frame, detect_all_objects(frame))
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

        rx1, ry1, rx2, ry2 = get_roi_bounds()
        weight = get_weight(cx, rx1, rx2)
        draw_divisions(frame, rx1, ry1, rx2, ry2)
        draw_labels(frame, detect_all_objects(frame))
        draw_detection_status(frame, mode, weight)

        if mode is not None:
            distance = get_distance()
            error = cx - target_x

            filtered_error = filtered_error * 0.7 + error * 0.3

            print(
                f"mode={mode}, cx={cx}, weight={weight}, target_x={target_x}, "
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


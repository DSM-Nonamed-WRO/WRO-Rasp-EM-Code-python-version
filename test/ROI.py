import cv2
import numpy as np

from HSV import make_red_mask, make_green_mask

# ===== 카메라 / 검출 설정 =====
WIDTH = 320
HEIGHT = 240
MIN_AREA = 500

# ===== ROI 영역 (화면 중앙에 세로로 긴 직사각형) =====
# 320x240 화면 중앙 기준, 가로 110 / 세로 170 픽셀
ROI_WIDTH = 110
ROI_HEIGHT = 170


def clean_mask(mask):
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    return mask


def get_roi_bounds():
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    x1 = center_x - ROI_WIDTH // 2
    x2 = center_x + ROI_WIDTH // 2
    y1 = center_y - ROI_HEIGHT // 2
    y2 = center_y + ROI_HEIGHT // 2
    return x1, y1, x2, y2


def detect_object(frame, color_mode):
    x1, y1, x2, y2 = get_roi_bounds()
    roi = frame[y1:y2, x1:x2]          # ROI만 잘라냄

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

    # ROI 기준 좌표
    x, y, w, h = cv2.boundingRect(largest)

    # ★ 전체 프레임 기준으로 변환 (offset 더하기)
    x += x1
    y += y1
    cx = x + w // 2
    cy = y + h // 2

    return True, cx, area, mask, (x, y, w, h, cx, cy)


def detect_all_objects(frame):
    # 화면 전체에서 빨강/초록 객체를 모두 찾아 리스트로 반환 (ROI 안/밖 상관없음)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    objects = []
    for color_mode, mask_func in (("RED", make_red_mask), ("GREEN", make_green_mask)):
        mask = clean_mask(mask_func(hsv))

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for c in contours:
            area = cv2.contourArea(c)
            if area < MIN_AREA:
                continue

            x, y, w, h = cv2.boundingRect(c)
            objects.append({
                "color": color_mode,
                "x": x,
                "y": y,
                "w": w,
                "h": h,
                "cx": x + w // 2,
                "cy": y + h // 2,
                "area": area,
            })

    return objects


def draw_roi(frame):
    x1, y1, x2, y2 = get_roi_bounds()
    # 하얀색 ROI 박스 (잘 보이게 두껍게)
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)


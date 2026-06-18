ROI_X_START = 0.0 
ROI_X_END   = 1.0
ROI_Y_START = 0.35
ROI_Y_END   = 0.95 

def get_roi_bounds():
    x1 = int(WIDTH * ROI_X_START)
    x2 = int(WIDTH * ROI_X_END)
    y1 = int(HEIGHT * ROI_Y_START)
    y2 = int(HEIGHT * ROI_Y_END)
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

    # ★ 전체 프레임 기준으로 변환 (offset 더하기) — 이게 제일 중요
    x += x1
    y += y1
    cx = x + w // 2
    cy = y + h // 2

    return True, cx, area, mask, (x, y, w, h, cx, cy)

def draw_roi(frame):
    x1, y1, x2, y2 = get_roi_bounds()
    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 1)

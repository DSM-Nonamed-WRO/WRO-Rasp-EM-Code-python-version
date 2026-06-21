import cv2

# ROI 가로를 몇 등분할지
DIVISIONS = 10

# 각 구간의 가중치 (왼쪽 -> 오른쪽)
# 중앙 = 1 (정면, 보정 거의 안 함), 가장자리 = 10 (많이 틀어짐 -> 크게 보정)
# 예) 가로 100 기준: 50=1, 20/80=8, 0/100=10
SECTION_WEIGHTS = [10, 9, 8, 4, 1, 1, 4, 8, 9, 10]


def get_section_index(cx, x1, x2):
    # 기둥 중심 cx(전체 프레임 기준)가 ROI의 몇 번째 구간에 있는지 반환
    if cx is None or cx < x1 or cx >= x2:
        return None

    roi_width = x2 - x1
    rel = cx - x1
    index = int(rel / roi_width * DIVISIONS)

    if index >= DIVISIONS:
        index = DIVISIONS - 1
    return index


def get_weight(cx, x1, x2):
    # 기둥이 있는 구간의 가중치 반환 (없으면 None)
    index = get_section_index(cx, x1, x2)
    if index is None:
        return None
    return SECTION_WEIGHTS[index]


def draw_divisions(frame, x1, y1, x2, y2):
    # 구간 경계선을 아주 얇고 희미하게(반투명) 표시
    step = (x2 - x1) / DIVISIONS

    overlay = frame.copy()
    for i in range(1, DIVISIONS):
        sx = int(x1 + step * i)
        cv2.line(overlay, (sx, y1), (sx, y2), (200, 200, 200), 1)

    alpha = 0.2  # 0 = 안 보임, 1 = 진함 (작을수록 희미)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


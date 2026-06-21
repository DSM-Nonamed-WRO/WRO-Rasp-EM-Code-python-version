import cv2
import numpy as np

# ===== 빨강 HSV 범위 (빨강은 0/180 양쪽에 걸쳐서 2구간) =====
LOWER_RED1 = np.array([0, 120, 70])
UPPER_RED1 = np.array([10, 255, 255])
LOWER_RED2 = np.array([170, 120, 70])
UPPER_RED2 = np.array([180, 255, 255])

# ===== 초록 HSV 범위 =====
LOWER_GREEN = np.array([40, 81, 28])
UPPER_GREEN = np.array([108, 255, 212])


def make_red_mask(hsv):
    mask1 = cv2.inRange(hsv, LOWER_RED1, UPPER_RED1)
    mask2 = cv2.inRange(hsv, LOWER_RED2, UPPER_RED2)
    return cv2.bitwise_or(mask1, mask2)


def make_green_mask(hsv):
    return cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)


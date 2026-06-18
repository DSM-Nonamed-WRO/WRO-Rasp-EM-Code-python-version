import cv2
import pygame
import numpy as np

CAMERA_INDEX = 0
CAM_WIDTH = 640
CAM_HEIGHT = 480
FPS = 30

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 760

PANEL_X = 680
SLIDER_X = 760
SLIDER_W = 280
VALUE_X = 1060

pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("HSV Color Tuner")
font = pygame.font.SysFont("malgungothic", 22)
small_font = pygame.font.SysFont("malgungothic", 18)
clock = pygame.time.Clock()

cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
cap.set(cv2.CAP_PROP_FPS, FPS)

if not cap.isOpened():
    print("Camera open failed")
    pygame.quit()
    exit()

h_min, h_max = 0, 10
s_min, s_max = 100, 255
v_min, v_max = 100, 255

dragging = None


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def cv_to_surface(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb = np.rot90(rgb)
    return pygame.surfarray.make_surface(rgb)


def draw_text(text, x, y, color=(230, 230, 230), size="normal"):
    f = small_font if size == "small" else font
    surface = f.render(text, True, color)
    screen.blit(surface, (x, y))


def draw_slider(name, value, min_v, max_v, y):
    pygame.draw.line(screen, (90, 90, 90), (SLIDER_X, y), (SLIDER_X + SLIDER_W, y), 8)

    ratio = (value - min_v) / (max_v - min_v)
    knob_x = int(SLIDER_X + ratio * SLIDER_W)

    pygame.draw.line(screen, (60, 130, 255), (SLIDER_X, y), (knob_x, y), 8)
    pygame.draw.circle(screen, (240, 240, 240), (knob_x, y), 10)
    pygame.draw.circle(screen, (60, 130, 255), (knob_x, y), 7)

    draw_text(name, PANEL_X, y - 14, size="small")
    pygame.draw.rect(screen, (20, 25, 30), (VALUE_X, y - 18, 70, 36), border_radius=5)
    draw_text(str(value), VALUE_X + 15, y - 13, size="small")

    return pygame.Rect(SLIDER_X, y - 15, SLIDER_W, 30)


def update_slider(mouse_x, min_v, max_v):
    ratio = (mouse_x - SLIDER_X) / SLIDER_W
    ratio = clamp(ratio, 0, 1)
    return int(min_v + ratio * (max_v - min_v))


running = True

while running:
    ret, frame = cap.read()

    if not ret:
        print("Frame read failed")
        break

    frame = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower = np.array([h_min, s_min, v_min])
    upper = np.array([h_max, s_max, v_max])

    mask = cv2.inRange(hsv, lower, upper)
    mask_bgr = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

    result = cv2.bitwise_and(frame, frame, mask=mask)

    screen.fill((18, 22, 27))

    draw_text("원본 영상 (Camera)", 30, 20)
    screen.blit(cv_to_surface(frame), (30, 60))

    draw_text("마스크 (Mask)", 30, 560)
    mask_small = cv2.resize(mask_bgr, (320, 160))
    screen.blit(cv_to_surface(mask_small), (30, 590))

    draw_text("HSV 범위 조절", PANEL_X, 30, (80, 150, 255))

    draw_text("Min (최소값)", PANEL_X, 80, (80, 150, 255), "small")
    rect_h_min = draw_slider("H Min", h_min, 0, 179, 130)
    rect_s_min = draw_slider("S Min", s_min, 0, 255, 180)
    rect_v_min = draw_slider("V Min", v_min, 0, 255, 230)

    draw_text("Max (최대값)", PANEL_X, 290, (80, 150, 255), "small")
    rect_h_max = draw_slider("H Max", h_max, 0, 179, 340)
    rect_s_max = draw_slider("S Max", s_max, 0, 255, 390)
    rect_v_max = draw_slider("V Max", v_max, 0, 255, 440)

    draw_text("현재 HSV 범위", PANEL_X, 520, (80, 150, 255))
    draw_text(f"H: {h_min} ~ {h_max}", PANEL_X, 570, (255, 70, 70))
    draw_text(f"S: {s_min} ~ {s_max}", PANEL_X + 220, 570, (70, 255, 120))
    draw_text(f"V: {v_min} ~ {v_max}", PANEL_X + 440, 570, (70, 150, 255))

    draw_text("S: 값 출력 | Q: 종료", PANEL_X, 650, (200, 200, 200), "small")

    pygame.display.update()

    sliders = {
        "h_min": rect_h_min,
        "s_min": rect_s_min,
        "v_min": rect_v_min,
        "h_max": rect_h_max,
        "s_max": rect_s_max,
        "v_max": rect_v_max,
    }

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                running = False

            elif event.key == pygame.K_s:
                print("Use this HSV range:")
                print(f"lower = np.array([{h_min}, {s_min}, {v_min}])")
                print(f"upper = np.array([{h_max}, {s_max}, {v_max}])")

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            for name, rect in sliders.items():
                if rect.collidepoint(mx, my):
                    dragging = name

        elif event.type == pygame.MOUSEBUTTONUP:
            dragging = None

        elif event.type == pygame.MOUSEMOTION and dragging:
            mx, my = event.pos

            if dragging == "h_min":
                h_min = update_slider(mx, 0, 179)
            elif dragging == "h_max":
                h_max = update_slider(mx, 0, 179)
            elif dragging == "s_min":
                s_min = update_slider(mx, 0, 255)
            elif dragging == "s_max":
                s_max = update_slider(mx, 0, 255)
            elif dragging == "v_min":
                v_min = update_slider(mx, 0, 255)
            elif dragging == "v_max":
                v_max = update_slider(mx, 0, 255)

    clock.tick(FPS)

cap.release()
pygame.quit()
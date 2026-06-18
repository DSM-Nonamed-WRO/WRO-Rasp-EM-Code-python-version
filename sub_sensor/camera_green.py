import cv2
import numpy as np

WIDTH = 320
HEIGHT = 240

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
cap.set(cv2.CAP_PROP_FPS, 30)

print(
    f"Resolution: "
    f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x"
    f"{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}"
)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_green = np.array([40, 81, 28])
    upper_green = np.array([108, 255, 212])

    mask = cv2.inRange(hsv, lower_green, upper_green)

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    result = cv2.bitwise_and(frame, frame, mask=mask)

    cv2.imshow("Camera", frame)
    cv2.imshow("Green Mask", mask)
    cv2.imshow("Green Detection", result)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
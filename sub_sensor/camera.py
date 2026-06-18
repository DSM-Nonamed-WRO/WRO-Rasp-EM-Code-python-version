import cv2

WIDTH = 320
HEIGHT = 240

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)

print(f"Actual Resolution: "
      f"{int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}x"
      f"{int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))}")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    cv2.imshow("Camera View", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

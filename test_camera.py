import cv2

camera = cv2.VideoCapture(0)

if not camera.isOpened():
    print("ERROR: Could not open the camera.")
    exit()

window_name = "FlowMate Camera Test"

cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

print("Camera opened successfully.")
print("Press Q to close.")

while True:
    success, frame = camera.read()

    if not success:
        print("ERROR: Could not read a frame.")
        break

    cv2.imshow(window_name, frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()

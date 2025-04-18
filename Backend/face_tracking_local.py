import cv2

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Failed to open webcam.")
else:
    print("✅ Webcam is working!")

cap.release()

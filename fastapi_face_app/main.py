from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import cv2
import face_recognition
from deepface import DeepFace
import numpy as np
import io

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# Load reference encoding
reference_image = face_recognition.load_image_file("reference.jpg")
reference_encoding = face_recognition.face_encodings(reference_image)[0]

# Shared status data
latest_data = {
    "emotion": "N/A",
    "face_dir": "N/A",
    "eye_dir": "N/A",
    "face_count": 0,
    "match_status": "Unknown",
    "warning_count": 0  # New field
}


# Emotion detector
def detect_emotion(face_roi):
    try:
        if face_roi.size > 0:
            result = DeepFace.analyze(face_roi, actions=["emotion"], enforce_detection=False)
            return result[0]["dominant_emotion"]
    except Exception as e:
        print("Emotion detection failed:", e)
    return "Unknown"

# Core video generator
def generate_frames():
    global latest_data
    cap = cv2.VideoCapture(0)
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")

    while True:
        success, frame = cap.read()
        if not success:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        latest_data["face_count"] = len(face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            match = face_recognition.compare_faces([reference_encoding], face_encoding)[0]
            color = (0, 255, 0) if match else (0, 0, 255)
            label = "MATCH" if match else "NO MATCH"
            latest_data["match_status"] = label

            face_roi = frame[top:bottom, left:right]
            emotion = detect_emotion(face_roi)
            latest_data["emotion"] = emotion

            face_dir = "Center"
            eye_dir = "Center"

            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                face_center_x = (left + right) // 2
                frame_center_x = frame.shape[1] // 2

                if face_center_x < frame_center_x - 100:
                    face_dir = "Left"
                elif face_center_x > frame_center_x + 100:
                    face_dir = "Right"

                roi_gray = gray[top:bottom, left:right]
                eyes = eye_cascade.detectMultiScale(roi_gray)

                for (ex, ey, ew, eh) in eyes:
                    eye_center_x = ex + ew // 2
                    eye_center_y = ey + eh // 2

                    eye_move_threshold_x = ew * 0.3
                    eye_move_threshold_y = eh * 0.2

                    if eye_center_x < ex + eye_move_threshold_x:
                        eye_dir = "Left"
                    elif eye_center_x > ex + ew - eye_move_threshold_x:
                        eye_dir = "Right"
                    elif eye_center_y < ey + eye_move_threshold_y:
                        eye_dir = "Up"
                    elif eye_center_y > ey + eh - eye_move_threshold_y:
                        eye_dir = "Down"
                    else:
                        eye_dir = "Center"
                    break
            except Exception as e:
                print("Direction detection error:", e)

            latest_data["face_dir"] = face_dir
            latest_data["eye_dir"] = eye_dir

            # Visuals
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, label, (left, top - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            cv2.putText(frame, f"{face_dir}, {eye_dir}", (left, top - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(frame, f"Emotion: {emotion}", (left, top - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        _, buffer = cv2.imencode(".jpg", frame)
        frame = buffer.tobytes()

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")

    cap.release()
    cv2.destroyAllWindows()

# Routes
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/status")
async def get_status():
    return JSONResponse(content=latest_data)

@app.get("/malpractice")
async def detect_malpractice():
    face_count = latest_data["face_count"]
    face_dir = latest_data["face_dir"]
    eye_dir = latest_data["eye_dir"]
    emotion = latest_data["emotion"]
    match_status = latest_data["match_status"]

    # Default verdict
    verdict = "Verified"

    # Malpractice detection logic
    if face_count == 0:
        verdict = "No person in frame"
    elif match_status != "MATCH":
        verdict = "Unverified person"
    elif face_dir != "Center" or eye_dir not in ["Center", "Up"]:
        if emotion.lower() in ["nervous", "fear", "angry", "surprise"]:
            verdict = "Suspicious behavior detected"
        else:
            verdict = "Face not centered or eye direction off"

    # Initialize last_verdict if not present
    if "last_verdict" not in latest_data:
        latest_data["last_verdict"] = ""

    # Increment warning_count only when verdict changes and it's not "Verified"
    if verdict != "Verified" and verdict != latest_data["last_verdict"]:
        latest_data["warning_count"] += 1

    # Update last_verdict
    latest_data["last_verdict"] = verdict

    return {
        "verdict": verdict,
        "warning_count": latest_data["warning_count"],
        "details": {
            "face_count": face_count,
            "face_direction": face_dir,
            "eye_direction": eye_dir,
            "emotion": emotion,
            "match_status": match_status
        }
    }


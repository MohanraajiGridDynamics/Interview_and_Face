from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import cv2
import face_recognition
from deepface import DeepFace
import numpy as np

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or ["http://localhost:3000"]
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
    "match": "N/A"
}

def detect_info(frame, face_location, face_encoding):
    global latest_data
    top, right, bottom, left = face_location
    face_img = frame[top:bottom, left:right]

    match = face_recognition.compare_faces([reference_encoding], face_encoding)[0]

    try:
        analysis = DeepFace.analyze(face_img, actions=['emotion'], enforce_detection=False)
        emotion = analysis[0]['dominant_emotion']
    except:
        emotion = "?"

    face_center = (left + right) // 2
    frame_center = frame.shape[1] // 2
    face_dir = "Center"
    if face_center < frame_center - 80:
        face_dir = "Left"
    elif face_center > frame_center + 80:
        face_dir = "Right"

    eye_dir = "Center"  # dummy

    latest_data.update({
        "emotion": emotion,
        "face_dir": face_dir,
        "eye_dir": eye_dir,
        "match": "MATCH" if match else "NO MATCH"
    })

    color = (0, 255, 0) if match else (0, 0, 255)
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
    cv2.putText(frame, f"{emotion} | {latest_data['match']}", (left, top - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def gen_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb)
        face_encodings = face_recognition.face_encodings(rgb, face_locations)

        for loc, enc in zip(face_locations, face_encodings):
            detect_info(frame, loc, enc)

        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(gen_frames(), media_type="multipart/x-mixed-replace; boundary=frame")

@app.get("/status")
async def get_status():
    return JSONResponse(content=latest_data)

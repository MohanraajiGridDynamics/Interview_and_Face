from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from ai_interviewer import start_interview_ws

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/interview/")
async def websocket_interview(websocket: WebSocket):
    #await websocket.accept()
    try:
        await start_interview_ws(websocket, skill="Python", num_questions=3)
    except Exception as e:
        await websocket.send_json({"sender": "System", "message": f"Error: {str(e)}"})
        await websocket.close()

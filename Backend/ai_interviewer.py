import openai
import azure.cognitiveservices.speech as speechsdk
import asyncio
from dotenv import load_dotenv
import os
import difflib
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta


load_dotenv()

# Azure Config
SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME")

client = openai.AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-01"
)

speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)

def text_to_speech_blocking(text):
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    synthesizer.speak_text_async(text).get()

async def text_to_speech(text):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, text_to_speech_blocking, text)


def speech_to_text_blocking():
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)
    print("Listening for response... Speak now.")
    result = speech_recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    else:
        return ""

async def speech_to_text():
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, speech_to_text_blocking)


def generate_follow_up_question(skill, previous_answer, asked_questions):
    prompt = f"""
You are an AI technical interviewer specialized in {skill}.

Based on the candidate's latest answer: "{previous_answer}", generate a precise and relevant follow-up question.
The follow-up should:
1. Explore areas where the candidate seemed less confident
2. Dive deeper into interesting points they mentioned
3. Test both theoretical knowledge and practical application
4. Avoid repetition of previously asked questions

Only return the question. Do not include any explanation or context.
"""
    messages = [
        {"role": "system", "content": "You are a professional AI interviewer."},
        {"role": "user", "content": prompt}
    ]
    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT_NAME,
        messages=messages,
        temperature=0.5,
        max_tokens=150
    )
    follow_up_question = response.choices[0].message.content.strip()

    # Ensure the follow-up question hasn't been asked yet
    if follow_up_question not in asked_questions:
        asked_questions.add(follow_up_question)
        return follow_up_question
    else:
        # If repeated, recursively generate a new one
        return generate_follow_up_question(skill, previous_answer, asked_questions)


def generate_feedback_and_score(answer, skill):
    prompt = f"""
You are a technical interviewer. Analyze the following candidate answer for the skill {skill}:

"{answer}"

Provide:
1. A brief professional feedback.
2. A confidence score (0 to 100).
3. Two strengths (if any).
4. Two areas of improvement.

Only output in JSON format as:
{{
  "feedback": "...",
  "confidence": 87,
  "strengths": ["...", "..."],
  "improvements": ["...", "..."]
}}
"""
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=AZURE_DEPLOYMENT_NAME,
        messages=messages,
        temperature=0.5,
        max_tokens=300
    )
    return eval(response.choices[0].message.content.strip())


def detect_plagiarism(answer):
    known_sources = [
        "In Python, a list is a mutable sequence type...",
        "A tuple is immutable and used to store constant data...",
        "To iterate over a list, we use a for loop..."
    ]
    for source in known_sources:
        similarity = difflib.SequenceMatcher(None, answer.lower(), source.lower()).ratio()
        if similarity > 0.9:
            return True
    return False


def generate_final_report(skill, feedback_data, questions):
    report = f"Interview Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"Skill Evaluated: {skill}\n"
    report += "-" * 50 + "\n"
    total_score = 0

    # Add questions and answers to the report
    for idx, data in enumerate(feedback_data):
        report += f"\nQuestion {idx + 1}: {questions[idx]}\n"  # Include the question from questions_list
        report += f"Answer: {data['answer']}\n"
        report += f"Feedback: {data['feedback']}\n"
        report += f"Confidence Score: {data['confidence']}\n"
        report += f"Strengths: {', '.join(data['strengths'])}\n"
        report += f"Areas for Improvement: {', '.join(data['improvements'])}\n"
        report += f"Plagiarism Suspected: {'Yes' if data['plagiarized'] else 'No'}\n"
        report += "-" * 50 + "\n"
        total_score += data['confidence']

    average_score = total_score / len(feedback_data)
    report += f"\nOverall Score: {average_score:.2f} / 100\n"

    if average_score >= 85:
        report += "Recommendation: Strong candidate for the role.\n"
    elif average_score >= 60:
        report += "Recommendation: Potential candidate with some gaps.\n"
    else:
        report += "Recommendation: Not recommended based on current evaluation.\n"

    # Generate the PDF
    create_pdf_report(report)
    return report


def create_pdf_report(report):
    file_name = f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    c = canvas.Canvas(file_name, pagesize=letter)
    c.setFont("Helvetica", 10)
    width, height = letter

    # Starting position for the content
    y_position = height - 40
    line_height = 12

    # Split the report into lines and write each line to the PDF
    for line in report.split("\n"):
        if y_position < 40:  # Prevent content from going off the page
            c.showPage()
            c.setFont("Helvetica", 10)
            y_position = height - 40
        c.drawString(40, y_position, line)
        y_position -= line_height

    # Save the PDF
    c.save()
    print(f"Report saved as {file_name}")


async def start_interview_ws(websocket, skill="Python", duration_minutes=30, num_questions: int = None):
    feedback_data = []
    questions_list = []
    asked_questions = set()
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Initial question
    await websocket.accept()
    await websocket.send_json({"sender": "AI", "message": f"Can you explain your experience with {skill}?"})
    await text_to_speech(f"Can you explain your experience with {skill}?")
    questions_list.append(f"Can you explain your experience with {skill}?")
    asked_questions.add(f"Can you explain your experience with {skill}?")
    
    # Continue interview until duration expires
    while datetime.now() < end_time:
        candidate_answer = await speech_to_text()
        await websocket.send_json({"sender": "Candidate", "message": candidate_answer})
        
        # Process answer and generate feedback
        analysis = generate_feedback_and_score(candidate_answer, skill)
        analysis["answer"] = candidate_answer
        analysis["plagiarized"] = detect_plagiarism(candidate_answer)
        feedback_data.append(analysis)
        
        # Check if we still have time for another question
        if datetime.now() < end_time - timedelta(minutes=2):  # Buffer time for final question
            follow_up = generate_follow_up_question(skill, candidate_answer, asked_questions)
            await websocket.send_json({"sender": "AI", "message": follow_up})
            await text_to_speech(follow_up)
            questions_list.append(follow_up)
        else:
            break
    
    # Closing remarks
    closing = "Thank you for your time. Our HR team will contact you with further updates."
    await websocket.send_json({"sender": "AI", "message": closing})
    await text_to_speech(closing)
    
    # Generate final report
    report = generate_final_report(skill, feedback_data, questions_list)
    print("\n\n==== Final Interview Report ====\n")
    print(report)
    
    # Send report URL to client
    await websocket.send_json({"sender": "System", "message": "Interview completed. Report generated."})

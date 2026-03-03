from fastapi import FastAPI, Depends, Form, Request, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import random
import string

import models
import models_staff
from database import engine, SessionLocal
from database_staff import engine_staff, SessionLocalStaff
import bot

# Create BOTH databases
models.Base.metadata.create_all(bind=engine)
models_staff.BaseStaff.metadata.create_all(bind=engine_staff)

app = FastAPI(title="OneTrip API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_staff_db():
    db = SessionLocalStaff()
    try:
        yield db
    finally:
        db.close()

class LoginRequest(BaseModel):
    username: str
    password: str

@app.get("/")
def read_root():
    return {"message": "OneTrip API is Active"}

@app.post("/seed")
def seed_database(db: Session = Depends(get_db), staff_db: Session = Depends(get_staff_db)):
    msg = ""
    # Seed Citizens DB
    if db.query(models.Service).count() == 0:
        db.add(models.Service(
            name_en="Income Certificate", required_docs_en="1. Aadhaar Card\n2. Address Proof\n3. Salary Slip/Affidavit",
            name_kn="ಆದಾಯ ಪ್ರಮಾಣಪತ್ರ", required_docs_kn="೧. ಆಧಾರ್ ಕಾರ್ಡ್\n೨. ವಿಳಾಸ ಪುರಾವೆ\n೩. ಆಫಿಡವಿಟ್"
        ))
        db.add(models.Service(
            name_en="Ration Card", required_docs_en="1. Aadhaar Card\n2. Passport Photos\n3. Address Proof",
            name_kn="ಪಡಿತರ ಚೀಟಿ", required_docs_kn="೧. ಆಧಾರ್ ಕಾರ್ಡ್\n೨. ಪಾಸ್‌ಪೋರ್ಟ್ ಫೋಟೋಗಳು\n೩. ವಿಳಾಸ ಪುರಾವೆ"
        ))
        db.commit()
        msg += "✅ Citizen Database seeded. "
    
    # Seed Staff DB
    if staff_db.query(models_staff.StaffAccount).count() == 0:
        staff_db.add(models_staff.StaffAccount(username="admin", password="password123", role="SuperAdmin", office_location="Office #04"))
        staff_db.commit()
        msg += "✅ Staff Database seeded. "
        
    return {"message": msg if msg else "⚠️ Databases already seeded."}

@app.post("/api/staff/login")
def login(request: LoginRequest, db: Session = Depends(get_staff_db)):
    account = db.query(models_staff.StaffAccount).filter(models_staff.StaffAccount.username == request.username).first()
    if account and account.password == request.password:
        return {"success": True, "token": "mock_secure_jwt_token_here", "user": {"username": account.username, "role": account.role, "office": account.office_location}}
    raise HTTPException(status_code=401, detail="Invalid Username or Password")

@app.get("/api/dashboard/appointments")
def get_appointments(db: Session = Depends(get_db)):
    appointments = db.query(models.Appointment).order_by(models.Appointment.date_created.desc()).all()
    
    results = []
    for appt in appointments:
        citizen = db.query(models.Citizen).filter(models.Citizen.id == appt.citizen_id).first()
        service = db.query(models.Service).filter(models.Service.id == appt.service_id).first()
        results.append({
            "id": appt.id,
            "name": citizen.name or citizen.phone_number,
            "location": citizen.location or "Unknown",
            "service": service.name_en,
            "token": appt.token_number,
            "status": appt.status,
            "time": appt.date_created.strftime("%H:%M %p"),
            "lang": citizen.language
        })
    return results

@app.put("/api/dashboard/appointments/{appointment_id}/complete")
def complete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if appt:
        appt.status = "COMPLETED"
        db.commit()
        return {"success": True}
    raise HTTPException(status_code=404, detail="Not Found")

@app.post("/api/webhook/twilio")
async def twilio_webhook(From: str = Form(...), Body: str = Form(None), db: Session = Depends(get_db)):
    phone_number = From.replace("whatsapp:", "")
    response_message = bot.process_incoming_message(db, phone_number, Body)
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?><Response><Message>{response_message}</Message></Response>"""
    return PlainTextResponse(content=twiml_response, media_type="application/xml")

@app.post("/api/webhook/twilio-voice")
async def twilio_voice_webhook(From: str = Form(...), Digits: str = Form(None), SpeechResult: str = Form(None), db: Session = Depends(get_db)):
    response_data = bot.process_incoming_voice(db, From, Digits, SpeechResult)
    text = response_data["text"]
    language_code = response_data.get("language_code", "en-US")
    input_type = response_data.get("input_type", "dtmf")
    
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Gather input="{input_type}" timeout="5" language="{language_code}" action="/api/webhook/twilio-voice">
        <Say language="{language_code}">{text}</Say>
    </Gather>
    <Redirect>/api/webhook/twilio-voice</Redirect>
</Response>"""
    return PlainTextResponse(content=twiml_response, media_type="application/xml")

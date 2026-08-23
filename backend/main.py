from fastapi import FastAPI, Depends, Form, Request, HTTPException, Header
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel
import random
import string
import os
import secrets
import time
import datetime

import models
import models_staff
from database import engine, SessionLocal
from database_staff import engine_staff, SessionLocalStaff
import bot
import security

# Create BOTH databases
models.Base.metadata.create_all(bind=engine)
models_staff.BaseStaff.metadata.create_all(bind=engine_staff)

app = FastAPI(title="OneTrip API")

# Configure secure origins
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security_scheme = HTTPBearer()

# Simple in-memory rate limiter for login attempts
login_attempts = {} # ip -> [timestamps]

def rate_limit_login(request: Request):
    ip = request.client.host
    now = time.time()
    # Clean old attempts (older than 60 seconds)
    attempts = [t for t in login_attempts.get(ip, []) if now - t < 60]
    if len(attempts) >= 5:
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again in a minute.")
    attempts.append(now)
    login_attempts[ip] = attempts

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    token = credentials.credentials
    payload = security.decode_jwt(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token or expired token")
    return payload

def verify_access(allowed_roles: list[str] = None):
    def dependency(current_user: dict = Depends(get_current_user)):
        if current_user.get("change_required"):
            raise HTTPException(status_code=403, detail="Password change required before accessing this resource")
        role = current_user.get("role")
        if allowed_roles and role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Permission denied")
        return current_user
    return dependency

TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

async def verify_twilio_signature(request: Request, x_twilio_signature: str = Header(None)):
    if TWILIO_AUTH_TOKEN:
        from twilio.request_validator import RequestValidator
        validator = RequestValidator(TWILIO_AUTH_TOKEN)
        
        # Get the form parameters
        form_data = await request.form()
        params = dict(form_data)
        
        # Build the exact request URL, taking reverse proxies into account
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("x-forwarded-host", request.url.netloc)
        url = f"{scheme}://{host}{request.url.path}"
        if request.url.query:
            url += f"?{request.url.query}"
            
        if not validator.validate(url, params, x_twilio_signature or ""):
            raise HTTPException(status_code=403, detail="Invalid Twilio request signature")

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

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@app.get("/")
def read_root():
    return {"message": "OneTrip API is Active"}

@app.post("/seed")
def seed_database(db: Session = Depends(get_db), staff_db: Session = Depends(get_staff_db)):
    if os.getenv("ALLOW_SEED", "false").lower() != "true":
        raise HTTPException(status_code=403, detail="Seeding is disabled. Set ALLOW_SEED=true to enable.")
        
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
        admin_password = os.getenv("SEED_ADMIN_PASSWORD")
        password_change_required = False
        if not admin_password:
            # Generate random password
            admin_password = secrets.token_urlsafe(10)
            password_change_required = True
        hashed = security.hash_password(admin_password)
        staff_db.add(models_staff.StaffAccount(
            username="admin", 
            password=hashed, 
            role="SuperAdmin", 
            office_location="Office #04",
            password_change_required=password_change_required
        ))
        staff_db.commit()
        msg += "✅ Staff Database seeded. Default admin created. "
        if password_change_required:
            return {"message": msg, "temp_admin_username": "admin", "temp_admin_password": admin_password}
        
    return {"message": msg if msg else "⚠️ Databases already seeded."}

@app.post("/api/staff/login")
def login(request: LoginRequest, fastapi_request: Request, db: Session = Depends(get_staff_db), _ = Depends(rate_limit_login)):
    account = db.query(models_staff.StaffAccount).filter(models_staff.StaffAccount.username == request.username).first()
    
    if account and security.verify_password(request.password, account.password):
        # Log successful login
        from models_staff import AuditLog
        log_entry = AuditLog(
            username=account.username,
            action="LOGIN_SUCCESS",
            details=f"Successful login from IP {fastapi_request.client.host}"
        )
        db.add(log_entry)
        db.commit()
        
        # Include change_required and office flag in token payload
        token_payload = {
            "sub": account.username, 
            "role": account.role, 
            "office": account.office_location
        }
        if account.password_change_required:
            token_payload["change_required"] = True
            
        token = security.create_jwt(token_payload)
        
        return {
            "success": True, 
            "token": token, 
            "change_required": account.password_change_required,
            "user": {
                "username": account.username, 
                "role": account.role, 
                "office": account.office_location
            }
        }
        
    # Log failed login
    from models_staff import AuditLog
    log_entry = AuditLog(
        username=request.username,
        action="LOGIN_FAILED",
        details=f"Failed login attempt from IP {fastapi_request.client.host}"
    )
    db.add(log_entry)
    db.commit()
    
    raise HTTPException(status_code=401, detail="Invalid Username or Password")

@app.post("/api/staff/change-password")
def change_password(request: ChangePasswordRequest, db: Session = Depends(get_staff_db), current_user: dict = Depends(get_current_user)):
    username = current_user.get("sub")
    account = db.query(models_staff.StaffAccount).filter(models_staff.StaffAccount.username == username).first()
    if not account or not security.verify_password(request.old_password, account.password):
        # Log failed password change
        from models_staff import AuditLog
        log_entry = AuditLog(
            username=username or "unknown",
            action="PASSWORD_CHANGE_FAILED",
            details="Failed password change: invalid old password"
        )
        db.add(log_entry)
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid old password")
        
    account.password = security.hash_password(request.new_password)
    account.password_change_required = False
    
    # Log successful password change
    from models_staff import AuditLog
    log_entry = AuditLog(
        username=username,
        action="PASSWORD_CHANGE_SUCCESS",
        details="Successfully changed password"
    )
    db.add(log_entry)
    db.commit()
    
    # Generate a NEW token without the change_required claim so the user doesn't have to re-login!
    new_token = security.create_jwt({
        "sub": account.username, 
        "role": account.role, 
        "office": account.office_location
    })
    
    return {
        "success": True, 
        "message": "Password changed successfully",
        "token": new_token
    }

@app.get("/api/dashboard/appointments")
def get_appointments(
    all: bool = False,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access(["SuperAdmin", "Officer", "Viewer"]))
):
    role = current_user.get("role")
    office = current_user.get("office")
    
    query = db.query(models.Appointment)
    if not all:
        # Filter by today's date in UTC
        now = datetime.datetime.utcnow()
        today_start = datetime.datetime(now.year, now.month, now.day, 0, 0, 0)
        query = query.filter(models.Appointment.date_created >= today_start)
        
    appointments = query.order_by(models.Appointment.date_created.desc()).all()
    
    results = []
    for appt in appointments:
        citizen = db.query(models.Citizen).filter(models.Citizen.id == appt.citizen_id).first()
        if not citizen:
            continue
            
        # Officer role filtering: only show appointments matching Officer's office
        if role == "Officer" and office:
            citizen_loc = (citizen.location or "").strip().lower()
            staff_office = office.strip().lower()
            if citizen_loc != staff_office:
                continue
                
        service = db.query(models.Service).filter(models.Service.id == appt.service_id).first()
        results.append({
            "id": appt.id,
            "name": citizen.name or citizen.phone_number,
            "location": citizen.location or "Unknown",
            "service": service.name_en if service else "Unknown Service",
            "token": appt.token_number,
            "status": appt.status,
            "time": appt.date_created.strftime("%H:%M %p"),
            "lang": citizen.language
        })
        
    # Apply standard pagination manually since we filtered in code
    paginated_results = results[offset : offset + limit]
    return paginated_results

@app.put("/api/dashboard/appointments/{appointment_id}/complete")
def complete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    staff_db: Session = Depends(get_staff_db),
    current_user: dict = Depends(verify_access(["SuperAdmin", "Officer"]))
):
    role = current_user.get("role")
    office = current_user.get("office")
    username = current_user.get("sub")
    
    appt = db.query(models.Appointment).filter(models.Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Not Found")
        
    citizen = db.query(models.Citizen).filter(models.Citizen.id == appt.citizen_id).first()
    
    # Officer role check
    if role == "Officer" and office:
        if not citizen or (citizen.location or "").strip().lower() != office.strip().lower():
            raise HTTPException(status_code=403, detail="Permission denied: appointment belongs to another office")
            
    appt.status = "COMPLETED"
    db.commit()
    
    # Write Audit Log
    from models_staff import AuditLog
    citizen_info = citizen.name or citizen.phone_number if citizen else "Unknown Citizen"
    log_entry = AuditLog(
        username=username,
        action="COMPLETE_APPOINTMENT",
        details=f"Completed appointment ID {appointment_id} for citizen: {citizen_info} at office: {office or 'SuperAdmin'}"
    )
    staff_db.add(log_entry)
    staff_db.commit()
    
    return {"success": True}

@app.get("/api/dashboard/citizens")
def get_citizens(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: dict = Depends(verify_access(["SuperAdmin", "Officer", "Viewer"]))
):
    role = current_user.get("role")
    office = current_user.get("office")
    
    citizens = db.query(models.Citizen).all()
    results = []
    for c in citizens:
        if role == "Officer" and office:
            citizen_loc = (c.location or "").strip().lower()
            staff_office = office.strip().lower()
            if citizen_loc != staff_office:
                continue
                
        service_name = "None"
        if c.selected_service_id:
            svc = db.query(models.Service).filter(models.Service.id == c.selected_service_id).first()
            if svc:
                service_name = svc.name_en
        results.append({
            "id": c.id,
            "phone_number": c.phone_number,
            "name": c.name or "N/A",
            "location": c.location or "N/A",
            "bot_state": c.bot_state,
            "language": c.language,
            "service": service_name
        })
        
    paginated_results = results[offset : offset + limit]
    return paginated_results

@app.get("/api/dashboard/services")
def get_services(db: Session = Depends(get_db), current_user: dict = Depends(verify_access(["SuperAdmin", "Officer", "Viewer"]))):
    services = db.query(models.Service).all()
    return [
        {
            "id": s.id,
            "name_en": s.name_en,
            "required_docs_en": s.required_docs_en,
            "name_kn": s.name_kn,
            "required_docs_kn": s.required_docs_kn
        }
        for s in services
    ]

@app.post("/api/webhook/twilio")
async def twilio_webhook(
    request: Request,
    From: str = Form(...),
    Body: str = Form(None),
    db: Session = Depends(get_db),
    _ = Depends(verify_twilio_signature)
):
    phone_number = From.replace("whatsapp:", "")
    response_message = bot.process_incoming_message(db, phone_number, Body)
    twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?><Response><Message>{response_message}</Message></Response>"""
    return PlainTextResponse(content=twiml_response, media_type="application/xml")

@app.post("/api/webhook/twilio-voice")
async def twilio_voice_webhook(
    request: Request,
    From: str = Form(...),
    Digits: str = Form(None),
    SpeechResult: str = Form(None),
    db: Session = Depends(get_db),
    _ = Depends(verify_twilio_signature)
):
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



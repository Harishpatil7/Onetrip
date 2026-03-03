from sqlalchemy.orm import Session
import models
import random
import string

# =========================================================================
# BOT TEXT LOGIC 
# =========================================================================
def process_incoming_message(db: Session, phone_number: str, message_body: str):
    citizen = db.query(models.Citizen).filter(models.Citizen.phone_number == phone_number).first()
    if not citizen:
        citizen = models.Citizen(phone_number=phone_number, bot_state="START")
        db.add(citizen)
        db.commit()
        db.refresh(citizen)
    
    raw_msg = message_body.strip() if message_body else ""
    msg_upper = raw_msg.upper()
    state = citizen.bot_state

    # Special Reset
    if msg_upper == "CANCEL" or msg_upper == "RESTART":
        citizen.bot_state = "START"
        db.commit()
        return "Conversation reset. Send 'Hi' to start over."

    if state == "START":
        citizen.bot_state = "WAITING_NAME"
        db.commit()
        return "Welcome to OneTrip! 🏢\nTo provide you better service, please tell us your *Full Name*."

    elif state == "WAITING_NAME":
        citizen.name = raw_msg.title()
        citizen.bot_state = "WAITING_LOCATION"
        db.commit()
        return f"Nice to meet you, {citizen.name}! Where are you from (Village or City)?"

    elif state == "WAITING_LOCATION":
        citizen.location = raw_msg.title()
        services = db.query(models.Service).all()
        if not services:
            return "Welcome to OneTrip! 🏢 We are currently setting up our system."
        
        responseText = f"Thank you, {citizen.name} from {citizen.location}.\n\nTell us what you need:\n"
        for idx, svc in enumerate(services, start=1):
            responseText += f"{idx}. {svc.name_en}\n"
        responseText += "\nReply with the NUMBER."
        
        citizen.bot_state = "SELECTING_SERVICE"
        db.commit()
        return responseText

    elif state == "SELECTING_SERVICE":
        if msg_upper.isdigit():
            services = db.query(models.Service).all()
            index = int(msg_upper) - 1
            if 0 <= index < len(services):
                service = services[index]
                citizen.selected_service_id = service.id
                citizen.bot_state = "CHECKING_DOCS"
                db.commit()
                return (f"You selected: {service.name_en}.\n\n"
                        f"Docs required:\n{service.required_docs_en}\n\n"
                        f"Have all ready? Reply YES or NO.")
            else:
                return "Invalid selection number."
        else:
            return "Please reply with a NUMBER."

    elif state == "CHECKING_DOCS":
        if msg_upper == "YES" or msg_upper == "Y":
            service = db.query(models.Service).filter(models.Service.id == citizen.selected_service_id).first()
            token = "".join(random.choices(string.ascii_uppercase + string.digits, k=5))
            db.add(models.Appointment(citizen_id=citizen.id, service_id=service.id, token_number=f"T-{token}"))
            citizen.bot_state = "START"
            citizen.selected_service_id = None
            db.commit()
            return f"✅ Confirmed!\nToken: T-{token}\nShow this at the office. 🚀"
        elif msg_upper == "NO" or msg_upper == "N":
            citizen.bot_state = "START"
            citizen.selected_service_id = None
            db.commit()
            return "No problem, take your time! Collect the docs first, and message again. Saved a trip! 🚗💨"
        else:
            return "Please reply YES or NO."
    else:
        citizen.bot_state = "START"
        db.commit()
        return "Sorry. Send 'Hi' to start over."


# =========================================================================
# BOT VOICE LOGIC (BILINGUAL: English + Kannada)
# =========================================================================
def process_incoming_voice(db: Session, phone_number: str, pressed_digit: str, speech_result: str):
    citizen = db.query(models.Citizen).filter(models.Citizen.phone_number == phone_number).first()
    if not citizen:
        citizen = models.Citizen(phone_number=phone_number, bot_state="SELECT_LANGUAGE")
        db.add(citizen)
        db.commit()
        db.refresh(citizen)
    
    state = citizen.bot_state
    lang_code = "kn-IN" if citizen.language == "KN" else "en-US"

    if state == "SELECT_LANGUAGE" or pressed_digit is None and state == "SELECT_LANGUAGE":
        voice_text = "Welcome to One Trip. For English, press 1. ಕನ್ನಡಕ್ಕಾಗಿ, ಎರಡು ಅನ್ನು ಒತ್ತಿರಿ"
        citizen.bot_state = "SELECTING_SERVICE" # Advance state behind the scenes
        citizen.language = "PENDING"
        db.commit()
        return {"text": voice_text, "language_code": "kn-IN", "input_type": "dtmf"}

    elif citizen.language == "PENDING" and state == "SELECTING_SERVICE":
        if pressed_digit == "1":
            citizen.language = "EN"
            lang_code = "en-US"
        elif pressed_digit == "2":
            citizen.language = "KN"
            lang_code = "kn-IN"
        else:
            return {"text": "Invalid press. For English, press 1. ಕನ್ನಡಕ್ಕಾಗಿ 2 ಒತ್ತಿರಿ", "language_code": "kn-IN", "input_type": "dtmf"}
        
        citizen.bot_state = "WAITING_NAME"
        db.commit()
        
        if citizen.language == "EN":
            return {"text": "Please say your full name clearly after the beep.", "language_code": "en-US", "input_type": "speech"}
        else:
            return {"text": "ದಯವಿಟ್ಟು ಬೀಪ್ ಶಬ್ದದ ನಂತರ ನಿಮ್ಮ ಹೆಸರನ್ನು ಹೇಳಿ", "language_code": "kn-IN", "input_type": "speech"}

    elif state == "WAITING_NAME":
        if speech_result:
            citizen.name = speech_result
            citizen.bot_state = "WAITING_LOCATION"
            db.commit()
            if citizen.language == "EN":
                msg = f"Thank you, {citizen.name}. Now, please say the name of your city or village after the beep."
            else:
                msg = f"ಧನ್ಯವಾದಗಳು, {citizen.name}. ಈಗ, ನಿಮ್ಮ ಊರಿನ ಹೆಸರನ್ನು ಹೇಳಿ."
            return {"text": msg, "language_code": lang_code, "input_type": "speech"}
        else:
            msg = "I didn't catch that. Please say your name clearly." if citizen.language == "EN" else "ನನಗೆ ಕೇಳಿಸಲಿಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಹೆಸರನ್ನು ಸ್ಪಷ್ಟವಾಗಿ ಹೇಳಿ."
            return {"text": msg, "language_code": lang_code, "input_type": "speech"}

    elif state == "WAITING_LOCATION":
        if speech_result:
            citizen.location = speech_result
            citizen.bot_state = "SELECTING_SERVICE"
            db.commit()
            
            services = db.query(models.Service).all()
            if citizen.language == "EN":
                voice_text = "Select a service. "
                for idx, svc in enumerate(services, start=1):
                    voice_text += f"For {svc.name_en}, press {idx}. "
            else:
                voice_text = "ಸೇವೆ ಆಯ್ಕೆ ಮಾಡಿ. "
                for idx, svc in enumerate(services, start=1):
                    voice_text += f"{svc.name_kn} ಗಾಗಿ, {idx} ಅನ್ನು ಒತ್ತಿರಿ. "
            
            return {"text": voice_text, "language_code": lang_code, "input_type": "dtmf"}
        else:
            msg = "I didn't catch that. Please say your location." if citizen.language == "EN" else "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಊರಿನ ಹೆಸರನ್ನು ಹೇಳಿ."
            return {"text": msg, "language_code": lang_code, "input_type": "speech"}

    elif state == "SELECTING_SERVICE":
        if pressed_digit and pressed_digit.isdigit():
            services = db.query(models.Service).all()
            index = int(pressed_digit) - 1
            if 0 <= index < len(services):
                service = services[index]
                citizen.selected_service_id = service.id
                citizen.bot_state = "CHECKING_DOCS"
                db.commit()
                
                if citizen.language == "EN":
                    docs = service.required_docs_en.replace('\n', ', ')
                    return {
                        "text": f"You need: {docs}. If you have all, press 1. If missing, press 2.", 
                        "language_code": "en-US",
                        "input_type": "dtmf"
                    }
                else:
                    docs = service.required_docs_kn.replace('\n', ', ')
                    text_kn = f"ನಿಮಗೆ ಇವು ಬೇಕು: {docs}. ಎಲ್ಲಾ ಇದ್ದರೆ 1 ಅನ್ನು ಒತ್ತಿರಿ. ಇಲ್ಲದಿದ್ದರೆ 2 ಅನ್ನು ಒತ್ತಿರಿ."
                    return {
                        "text": text_kn, 
                        "language_code": "kn-IN",
                        "input_type": "dtmf"
                    }
            else:
                msg = "Invalid. Try again." if citizen.language == "EN" else "ತಪ್ಪಾಗಿದೆ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ."
                return {"text": msg, "language_code": lang_code, "input_type": "dtmf"}
        else:
            msg = "Press a number." if citizen.language == "EN" else "ದಯವಿಟ್ಟು ಸಂಖ್ಯೆಯನ್ನು ಒತ್ತಿರಿ."
            return {"text": msg, "language_code": lang_code, "input_type": "dtmf"}

    elif state == "CHECKING_DOCS":
        if pressed_digit == "1":
            service = db.query(models.Service).filter(models.Service.id == citizen.selected_service_id).first()
            token = "".join(random.choices(string.digits, k=4))
            
            db.add(models.Appointment(citizen_id=citizen.id, service_id=service.id, token_number=f"T-{token}"))
            citizen.bot_state = "SELECT_LANGUAGE"
            citizen.selected_service_id = None
            citizen.language = "EN"
            db.commit()
            
            spoken_token = " ".join([d for d in token])
            if lang_code == "en-US":
                return {
                    "text": f"Confirmed! Your token is: T, {spoken_token}. Bring documents. Goodbye.",
                    "language_code": "en-US",
                    "input_type": "dtmf" 
                }
            else:
                return {
                    "text": f"ಖಚಿತಪಡಿಸಲಾಗಿದೆ! ನಿಮ್ಮ ಟೋಕನ್: T, {spoken_token}. ದಾಖಲೆಗಳನ್ನು ಕಚೇರಿಗೆ ತನ್ನಿ. ಧನ್ಯವಾದಗಳು.",
                    "language_code": "kn-IN",
                    "input_type": "dtmf"
                }

        elif pressed_digit == "2":
            citizen.bot_state = "SELECT_LANGUAGE"
            citizen.selected_service_id = None
            citizen.language = "EN"
            db.commit()
            if lang_code == "en-US":
                return {"text": "Collect documents first. Goodbye.", "language_code": "en-US", "input_type": "dtmf"}
            else:
                return {"text": "ಮೊದಲು ದಾಖಲೆಗಳನ್ನು ಸಂಗ್ರಹಿಸಿ. ಮತ್ತೆ ಕರೆ ಮಾಡಿ. ಧನ್ಯವಾದಗಳು.", "language_code": "kn-IN", "input_type": "dtmf"}

    else:
        citizen.bot_state = "SELECT_LANGUAGE"
        db.commit()
        return {"text": "Error. Goodbye.", "language_code": "en-US", "input_type": "dtmf"}

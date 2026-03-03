import requests
import time
import re

PHONE_NUMBER = "+910000000000"
URL = "http://localhost:8000/api/webhook/twilio"

def send_message(body):
    print(f"\n📱 Citizen sends: {body}")
    data = {"From": PHONE_NUMBER, "Body": body}
    response = requests.post(URL, data=data)
    match = re.search(r'<Message>(.*?)</Message>', response.text, re.DOTALL)
    if match:
        print(f"🤖 Bot replies:\n{match.group(1).strip()}\n")
    else:
        print(f"Server response: {response.text}")

print("=== STARTING ONETRIP SIMULATION (SMS) ===")

# Start Over
send_message("RESTART")
time.sleep(1)

send_message("Hi")
time.sleep(1)

send_message("Ramesh Kumar")
time.sleep(1)

send_message("Hubli")
time.sleep(1)

send_message("1")
time.sleep(1)

send_message("YES")

print("=== SIMULATION COMPLETE ===")

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from twilio.rest import Client
from dotenv import load_dotenv
import os
from datetime import datetime
import uuid

load_dotenv()

router = APIRouter()

account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
twilio_number = os.getenv("TWILIO_PHONE_NUMBER")

sms_logs = []

twilio_client = None
if account_sid and auth_token:
    try:
        twilio_client = Client(account_sid, auth_token)
    except Exception as e:
        print(f"Failed to initialize Twilio client: {str(e)}")

class SMSRequest(BaseModel):
    user_id: int
    to: str
    body: str

@router.post("/send")
def send_sms(payload: SMSRequest):
    try:
        sms_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            "id": sms_id,
            "user_id": payload.user_id,
            "to": payload.to,
            "body": payload.body,
            "sid": None,
            "created_at": timestamp
        }
        
        if twilio_client and twilio_number:
            message = twilio_client.messages.create(
                body=payload.body,
                from_=twilio_number,
                to=payload.to
            )
            log_entry["sid"] = message.sid
        else:
            print("Twilio not configured. SMS would have been sent to:", payload.to)
        
        sms_logs.append(log_entry)
        
        return {"message": "SMS processed", "sid": log_entry["sid"], "id": sms_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/{user_id}")
def get_sms_logs(user_id: int):
    """Get SMS logs for a user"""
    user_logs = [log for log in sms_logs if log["user_id"] == user_id]
    
    if not user_logs and os.getenv("VERCEL") == "1":
        sample_logs = [
            {
                "id": "sample-1",
                "user_id": user_id,
                "to": "+1234567890",
                "body": "This is a sample SMS notification",
                "sid": "sample-sid-1",
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "sample-2",
                "user_id": user_id,
                "to": "+1234567890", 
                "body": "Another sample SMS notification",
                "sid": "sample-sid-2",
                "created_at": datetime.now().isoformat()
            }
        ]
        return {"logs": sample_logs}
    
    return {"logs": user_logs}
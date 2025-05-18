# services/e_notif.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

router = APIRouter()

# In production with Vercel, we use in-memory storage instead of SQLite
# since Vercel has a read-only filesystem in production
email_notifications_db = []

# Email config
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM", "test@example.com"),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.example.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# Schemas
class EmailRequest(BaseModel):
    user_id: int
    email: EmailStr
    subject: str
    body: str

class EmailNotificationResponse(BaseModel):
    id: str
    user_id: int
    email_to: str
    subject: str
    body: str
    sent: bool
    created_at: str

@router.post("/send_email")
async def send_email(data: EmailRequest):
    try:
        # Create notification record
        notification_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        notification = {
            "id": notification_id,
            "user_id": data.user_id,
            "email_to": data.email,
            "subject": data.subject,
            "body": data.body,
            "sent": True,
            "created_at": timestamp
        }
        
        # Store in in-memory DB (will be lost when serverless function ends)
        # In a real application, you would store this in a persistent database
        email_notifications_db.append(notification)
        
        # Create and send email
        message = MessageSchema(
            subject=data.subject,
            recipients=[data.email],
            body=data.body,
            subtype="html"
        )
        
        try:
            fm = FastMail(conf)
            await fm.send_message(message)
        except Exception as email_error:
            # If email sending fails, we still create the notification
            # but mark it as not sent
            notification["sent"] = False
            
            # For real applications, log this error
            print(f"Email sending error: {str(email_error)}")
        
        return {"message": "Email notification processed", "notification_id": notification_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process email: {str(e)}")

@router.get("/users/{user_id}/notifications")
def get_user_notifications(user_id: int):
    """Get all email notifications for a user - for demo purposes returns test data in production"""
    # For Vercel deployment demo purposes, we'll return sample data
    # In a real application, you would fetch this from a database
    
    # Check if we have data in our in-memory store
    user_notifications = [n for n in email_notifications_db if n["user_id"] == user_id]
    
    # If no data, return sample data
    if not user_notifications and os.getenv("VERCEL") == "1":
        # Sample data for demo
        return [
            {
                "id": "sample-1",
                "user_id": user_id,
                "email_to": "user@example.com",
                "subject": "Welcome to Notifications",
                "body": "This is a sample email notification",
                "sent": True,
                "created_at": datetime.now().isoformat()
            },
            {
                "id": "sample-2",
                "user_id": user_id,
                "email_to": "user@example.com",
                "subject": "Your Account Update",
                "body": "This is another sample email notification",
                "sent": True,
                "created_at": datetime.now().isoformat()
            }
        ]
    
    return user_notifications
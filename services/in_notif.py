from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import os

router = APIRouter()

# In-memory storage for notifications (will be reset on each function execution in serverless)
notifications_db = []

class NotificationCreate(BaseModel):
    user_id: int
    title: str
    message: str
    notification_type: str = "info"  # info, warning, error, success
    link: Optional[str] = None

class Notification(BaseModel):
    id: str
    user_id: int
    title: str
    message: str
    notification_type: str
    link: Optional[str] = None
    read: bool = False
    created_at: datetime

@router.post("/create", response_model=Notification, status_code=status.HTTP_201_CREATED)
async def create_notification(notification: NotificationCreate):
    """Create a new in-app notification for a user"""
    new_notification = Notification(
        id=str(uuid.uuid4()),
        user_id=notification.user_id,
        title=notification.title,
        message=notification.message,
        notification_type=notification.notification_type,
        link=notification.link,
        read=False,
        created_at=datetime.now()
    )
    
    notifications_db.append(new_notification.dict())
    return new_notification

@router.get("/user/{user_id}", response_model=List[dict])
async def get_user_notifications(user_id: int, unread_only: bool = False):
    """Get all notifications for a user"""
    if unread_only:
        user_notifications = [n for n in notifications_db if n["user_id"] == user_id and not n["read"]]
    else:
        user_notifications = [n for n in notifications_db if n["user_id"] == user_id]
    
    # For Vercel deployment, if no notifications, return sample data
    if not user_notifications and os.getenv("VERCEL") == "1":
        # Create sample notifications for demonstration
        sample_notifications = [
            {
                "id": f"{user_id}-sample-1",
                "user_id": user_id,
                "title": "Welcome to the Notification System",
                "message": "This is a sample in-app notification. You can create more by using the form.",
                "notification_type": "info",
                "link": None,
                "read": False,
                "created_at": datetime.now().isoformat()
            },
            {
                "id": f"{user_id}-sample-2",
                "user_id": user_id,
                "title": "Tip: Try Different Notification Types",
                "message": "You can create notifications with different types: info, success, warning, and error.",
                "notification_type": "success",
                "link": None,
                "read": False,
                "created_at": datetime.now().isoformat()
            },
            {
                "id": f"{user_id}-sample-3",
                "user_id": user_id,
                "title": "Check Out the History Tab",
                "message": "View all your notifications in the History tab and manage their status.",
                "notification_type": "warning",
                "link": None,
                "read": True,
                "created_at": datetime.now().isoformat()
            }
        ]
        return sample_notifications
    
    # Sort by created_at (newest first)
    user_notifications.sort(key=lambda x: x["created_at"], reverse=True)
    return user_notifications

@router.put("/{notification_id}/mark-read")
async def mark_notification_read(notification_id: str):
    """Mark a notification as read"""
    for notification in notifications_db:
        if notification["id"] == notification_id:
            notification["read"] = True
            return {"success": True}
    
    # For Vercel, let's not throw errors if the notification is not found
    if os.getenv("VERCEL") == "1":
        return {"success": True, "note": "Sample notification marked as read"}
    
    raise HTTPException(status_code=404, detail="Notification not found")

@router.put("/user/{user_id}/mark-all-read")
async def mark_all_notifications_read(user_id: int):
    """Mark all user notifications as read"""
    updated_count = 0
    for notification in notifications_db:
        if notification["user_id"] == user_id and not notification["read"]:
            notification["read"] = True
            updated_count += 1
    
    return {"success": True, "marked_read_count": updated_count}

@router.delete("/{notification_id}")
async def delete_notification(notification_id: str):
    """Delete a notification"""
    global notifications_db
    original_length = len(notifications_db)
    notifications_db = [n for n in notifications_db if n["id"] != notification_id]
    
    # For Vercel, let's not throw errors if the notification is not found
    if len(notifications_db) == original_length and os.getenv("VERCEL") != "1":
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True}
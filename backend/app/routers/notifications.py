"""
Notifications API Router for Pulse AI
Handles in-app notifications for all user roles
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import User, Notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ==========================================
# Pydantic Schemas
# ==========================================

class NotificationResponse(BaseModel):
    id: int
    notification_type: str
    title: str
    message: Optional[str]
    related_user_id: Optional[int]
    related_user_name: Optional[str] = None
    is_read: bool
    priority: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class NotificationStats(BaseModel):
    total: int
    unread: int
    high_priority: int


# ==========================================
# Notification APIs
# ==========================================

@router.get("/{user_id}", response_model=List[NotificationResponse])
def get_notifications(
    user_id: int,
    unread_only: bool = Query(False),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """Get notifications for a user"""
    query = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_dismissed == False
    )
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(
        Notification.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    results = []
    for notif in notifications:
        related_user_name = None
        if notif.related_user_id:
            related_user = db.query(User).filter(User.id == notif.related_user_id).first()
            if related_user:
                related_user_name = related_user.name
        
        results.append(NotificationResponse(
            id=notif.id,
            notification_type=notif.notification_type,
            title=notif.title,
            message=notif.message,
            related_user_id=notif.related_user_id,
            related_user_name=related_user_name,
            is_read=notif.is_read,
            priority=notif.priority,
            created_at=notif.created_at
        ))
    
    return results


@router.get("/{user_id}/stats", response_model=NotificationStats)
def get_notification_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get notification statistics for a user"""
    base_query = db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_dismissed == False
    )
    
    total = base_query.count()
    unread = base_query.filter(Notification.is_read == False).count()
    high_priority = base_query.filter(
        Notification.priority.in_(["high", "critical"]),
        Notification.is_read == False
    ).count()
    
    return NotificationStats(
        total=total,
        unread=unread,
        high_priority=high_priority
    )


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    notification.read_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Notification marked as read"}


@router.post("/{user_id}/read-all")
def mark_all_notifications_read(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for a user"""
    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.is_read == False
    ).update({
        "is_read": True,
        "read_at": datetime.utcnow()
    })
    
    db.commit()
    
    return {"message": "All notifications marked as read"}


@router.post("/{notification_id}/dismiss")
def dismiss_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Dismiss a notification (hide from list)"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_dismissed = True
    db.commit()
    
    return {"message": "Notification dismissed"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Delete a notification permanently"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    db.delete(notification)
    db.commit()
    
    return {"message": "Notification deleted"}

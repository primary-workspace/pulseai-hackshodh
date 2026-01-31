"""
Notification Model for Pulse AI
Handles in-app notifications for all user roles
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Notification content
    notification_type = Column(String, nullable=False)  # anomaly, connection_request, alert, info
    title = Column(String, nullable=False)
    message = Column(Text, nullable=True)
    
    # Related entities
    related_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Patient who triggered
    related_care_score_id = Column(Integer, ForeignKey("care_scores.id"), nullable=True)
    
    # Status
    is_read = Column(Boolean, default=False)
    is_dismissed = Column(Boolean, default=False)
    
    # Priority
    priority = Column(String, default="normal")  # low, normal, high, critical
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    read_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="notifications", foreign_keys=[user_id])
    related_user = relationship("User", foreign_keys=[related_user_id])

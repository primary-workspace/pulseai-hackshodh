"""
Caretaker Profile Model for Pulse AI
Profile for family members/guardians who monitor patients
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class CaretakerProfile(Base):
    __tablename__ = "caretaker_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Personal details
    full_name = Column(String, nullable=False)
    relationship_type = Column(String, nullable=True)  # family, professional, friend
    phone_number = Column(String, nullable=True)
    
    # Preferences
    notification_preference = Column(String, default="all")  # all, critical_only, none
    
    # Meta
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="caretaker_profile")

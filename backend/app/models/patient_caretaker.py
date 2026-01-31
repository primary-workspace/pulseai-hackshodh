"""
Patient-Caretaker Relationship Model for Pulse AI
Manages connections between patients and their caretakers/family members
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class PatientCaretaker(Base):
    __tablename__ = "patient_caretakers"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    caretaker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Connection status
    status = Column(String, default="pending")  # pending, accepted, rejected
    access_level = Column(String, default="read")  # read, alerts_only
    
    # Timestamps
    invited_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    
    # Invitation details
    invitation_code = Column(String, nullable=True)
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    caretaker = relationship("User", foreign_keys=[caretaker_id])

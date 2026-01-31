"""
Doctor Profile Model for Pulse AI
Extended profile for doctors with medical credentials
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Professional details
    full_name = Column(String, nullable=False)
    specialization = Column(String, nullable=False)  # Cardiology, General Medicine, etc.
    qualification = Column(String, nullable=True)  # MBBS, MD, etc.
    
    # Hospital/Clinic details
    hospital_name = Column(String, nullable=True)
    hospital_address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, default="India")
    
    # Contact
    emergency_contact = Column(String, nullable=True)
    consultation_hours = Column(String, nullable=True)
    
    # Verification
    license_number = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    
    # Meta
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="doctor_profile")

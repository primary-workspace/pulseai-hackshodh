"""
User Model for Pulse AI
Supports multiple roles: patient, doctor, caretaker
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    CARETAKER = "caretaker"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Role management
    role = Column(String, default="patient")  # patient, doctor, caretaker
    role_verified = Column(Boolean, default=False)
    
    # Baseline values (learned over time) - for patients
    baseline_heart_rate = Column(Float, nullable=True)
    baseline_hrv = Column(Float, nullable=True)
    baseline_sleep_hours = Column(Float, nullable=True)
    baseline_activity_level = Column(Float, nullable=True)
    baseline_breathing_rate = Column(Float, nullable=True)
    baseline_bp_systolic = Column(Float, nullable=True)
    baseline_bp_diastolic = Column(Float, nullable=True)
    baseline_blood_sugar = Column(Float, nullable=True)
    
    # Relationships
    health_data = relationship("HealthData", back_populates="user")
    care_scores = relationship("CareScore", back_populates="user")
    escalations = relationship("Escalation", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")
    devices = relationship("DeviceRegistration", back_populates="user")
    
    # Role-specific profiles
    doctor_profile = relationship("DoctorProfile", back_populates="user", uselist=False)
    caretaker_profile = relationship("CaretakerProfile", back_populates="user", uselist=False)
    
    # Notifications
    notifications = relationship("Notification", back_populates="user", foreign_keys="Notification.user_id")

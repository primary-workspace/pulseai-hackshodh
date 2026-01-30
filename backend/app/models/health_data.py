"""
Health Data Model for Pulse AI
Stores wearable and manual health inputs
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class HealthData(Base):
    __tablename__ = "health_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    source = Column(String, default="wearable")  # wearable, manual, health_connect
    
    # Activity data
    steps = Column(Integer, nullable=True)  # Step count
    distance = Column(Float, nullable=True)  # Distance in meters
    calories_active = Column(Float, nullable=True)  # Active calories burned
    calories_total = Column(Float, nullable=True)  # Total calories burned
    activity_level = Column(Float, nullable=True)  # Active minutes or general activity
    
    # Vital signs
    heart_rate = Column(Float, nullable=True)  # BPM
    hrv = Column(Float, nullable=True)  # Heart Rate Variability in ms
    breathing_rate = Column(Float, nullable=True)  # Breaths per minute
    spo2 = Column(Float, nullable=True)  # Oxygen saturation percentage
    temperature = Column(Float, nullable=True)  # Body temperature in Celsius
    
    # Sleep data
    sleep_duration = Column(Float, nullable=True)  # Hours
    sleep_quality = Column(Float, nullable=True)  # 0-100 score
    
    # Blood metrics
    bp_systolic = Column(Float, nullable=True)
    bp_diastolic = Column(Float, nullable=True)
    blood_sugar = Column(Float, nullable=True)  # mg/dL
    
    # Body metrics
    weight = Column(Float, nullable=True)  # Weight in kg
    
    # Manual inputs
    symptoms = Column(Text, nullable=True)  # JSON array of symptoms
    
    # Computed flags
    is_anomaly = Column(Integer, default=0)  # 0=normal, 1=mild, 2=moderate, 3=severe
    
    # Relationship
    user = relationship("User", back_populates="health_data")


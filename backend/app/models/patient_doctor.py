"""
Patient-Doctor Relationship Model for Pulse AI
Manages connections between patients and their healthcare providers
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class PatientDoctor(Base):
    __tablename__ = "patient_doctors"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Connection status
    status = Column(String, default="pending")  # pending, accepted, rejected
    requested_by = Column(String, nullable=True)  # patient or doctor
    
    # Timestamps
    requested_at = Column(DateTime, default=datetime.utcnow)
    accepted_at = Column(DateTime, nullable=True)
    
    # Optional notes
    patient_notes = Column(String, nullable=True)  # Why connecting
    doctor_notes = Column(String, nullable=True)
    
    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])

"""
Caretakers API Router for Pulse AI
Handles caretaker profiles and patient monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.database import get_db
from app.models import User, CaretakerProfile, PatientCaretaker, HealthData, CareScore

router = APIRouter(prefix="/caretakers", tags=["Caretakers"])


# ==========================================
# Pydantic Schemas
# ==========================================

class CaretakerProfileCreate(BaseModel):
    full_name: str
    relationship_type: Optional[str] = None
    phone_number: Optional[str] = None
    notification_preference: str = "all"


class CaretakerProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    relationship_type: Optional[str]
    notification_preference: str
    
    class Config:
        from_attributes = True


class PatientStatusCard(BaseModel):
    patient_id: int
    patient_name: str
    risk_level: str  # stable, mild, moderate, high
    care_score: Optional[int]
    last_update: Optional[datetime]
    has_recent_anomaly: bool


# ==========================================
# Caretaker Dashboard APIs
# ==========================================

@router.get("/dashboard/patients/{caretaker_user_id}", response_model=List[PatientStatusCard])
def get_caretaker_patients(
    caretaker_user_id: int,
    db: Session = Depends(get_db)
):
    """Get simplified status cards for all linked patients"""
    # Verify caretaker exists
    caretaker = db.query(User).filter(
        User.id == caretaker_user_id, 
        User.role == "caretaker"
    ).first()
    
    if not caretaker:
        raise HTTPException(status_code=404, detail="Caretaker not found")
    
    # Get patient connections
    connections = db.query(PatientCaretaker).filter(
        PatientCaretaker.caretaker_id == caretaker_user_id,
        PatientCaretaker.status == "accepted"
    ).all()
    
    patients = []
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    for conn in connections:
        patient = db.query(User).filter(User.id == conn.patient_id).first()
        if not patient:
            continue
        
        # Get latest care score
        latest_score = db.query(CareScore).filter(
            CareScore.user_id == patient.id
        ).order_by(CareScore.timestamp.desc()).first()
        
        # Determine risk level
        care_score = latest_score.care_score if latest_score else 0
        if care_score >= 70:
            risk_level = "high"
        elif care_score >= 50:
            risk_level = "moderate"
        elif care_score >= 25:
            risk_level = "mild"
        else:
            risk_level = "stable"
        
        # Check for recent anomalies
        has_anomaly = db.query(HealthData).filter(
            HealthData.user_id == patient.id,
            HealthData.timestamp >= cutoff,
            HealthData.is_anomaly > 0
        ).first() is not None
        
        # Get last update
        last_data = db.query(HealthData).filter(
            HealthData.user_id == patient.id
        ).order_by(HealthData.timestamp.desc()).first()
        
        patients.append(PatientStatusCard(
            patient_id=patient.id,
            patient_name=patient.name,
            risk_level=risk_level,
            care_score=care_score if care_score > 0 else None,
            last_update=last_data.timestamp if last_data else None,
            has_recent_anomaly=has_anomaly
        ))
    
    # Sort by risk (highest first)
    risk_order = {"high": 0, "moderate": 1, "mild": 2, "stable": 3}
    patients.sort(key=lambda x: risk_order.get(x.risk_level, 4))
    
    return patients


@router.get("/dashboard/patients/{caretaker_user_id}/{patient_id}")
def get_patient_simplified_status(
    caretaker_user_id: int,
    patient_id: int,
    db: Session = Depends(get_db)
):
    """Get simplified health status for a specific patient (caretaker view)"""
    # Verify connection exists
    connection = db.query(PatientCaretaker).filter(
        PatientCaretaker.caretaker_id == caretaker_user_id,
        PatientCaretaker.patient_id == patient_id,
        PatientCaretaker.status == "accepted"
    ).first()
    
    if not connection:
        raise HTTPException(status_code=403, detail="No active connection with this patient")
    
    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Get latest care score
    latest_score = db.query(CareScore).filter(
        CareScore.user_id == patient_id
    ).order_by(CareScore.timestamp.desc()).first()
    
    # Determine risk level and message
    care_score = latest_score.care_score if latest_score else 0
    if care_score >= 70:
        risk_level = "high"
        status_message = "Requires immediate attention"
    elif care_score >= 50:
        risk_level = "moderate"
        status_message = "Monitoring recommended"
    elif care_score >= 25:
        risk_level = "mild"
        status_message = "Minor concerns detected"
    else:
        risk_level = "stable"
        status_message = "All vitals appear normal"
    
    # Last update time
    last_data = db.query(HealthData).filter(
        HealthData.user_id == patient_id
    ).order_by(HealthData.timestamp.desc()).first()
    
    return {
        "patient_id": patient.id,
        "patient_name": patient.name,
        "risk_level": risk_level,
        "status_message": status_message,
        "care_score": care_score if care_score > 0 else None,
        "last_update": last_data.timestamp if last_data else None,
        "care_score_explanation": latest_score.explanation if latest_score else None
    }


# ==========================================
# Caretaker Profile Management
# ==========================================

@router.post("/profile/{user_id}", response_model=CaretakerProfileResponse)
def create_caretaker_profile(
    user_id: int,
    profile: CaretakerProfileCreate,
    db: Session = Depends(get_db)
):
    """Create caretaker profile for a user"""
    # Check user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if profile already exists
    existing = db.query(CaretakerProfile).filter(CaretakerProfile.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Caretaker profile already exists")
    
    # Update user role
    user.role = "caretaker"
    
    # Create profile
    caretaker_profile = CaretakerProfile(
        user_id=user_id,
        **profile.dict()
    )
    
    db.add(caretaker_profile)
    db.commit()
    db.refresh(caretaker_profile)
    
    return caretaker_profile


@router.put("/profile/{user_id}", response_model=CaretakerProfileResponse)
def update_caretaker_profile(
    user_id: int,
    profile: CaretakerProfileCreate,
    db: Session = Depends(get_db)
):
    """Update existing caretaker profile"""
    existing = db.query(CaretakerProfile).filter(CaretakerProfile.user_id == user_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Caretaker profile not found")
    
    for key, value in profile.dict(exclude_unset=True).items():
        setattr(existing, key, value)
    
    existing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(existing)
    
    return existing


@router.get("/profile/{user_id}", response_model=CaretakerProfileResponse)
def get_caretaker_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get caretaker profile"""
    profile = db.query(CaretakerProfile).filter(CaretakerProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Caretaker profile not found")
    
    return profile

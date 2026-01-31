"""
Doctors API Router for Pulse AI
Handles doctor profiles, discovery, and patient management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import User, DoctorProfile, PatientDoctor, HealthData, CareScore

router = APIRouter(prefix="/doctors", tags=["Doctors"])


# ==========================================
# Pydantic Schemas
# ==========================================

class DoctorProfileCreate(BaseModel):
    full_name: str
    specialization: str
    qualification: Optional[str] = None
    hospital_name: Optional[str] = None
    hospital_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    emergency_contact: Optional[str] = None
    consultation_hours: Optional[str] = None
    license_number: Optional[str] = None


class DoctorProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: str
    specialization: str
    qualification: Optional[str]
    hospital_name: Optional[str]
    city: Optional[str]
    state: Optional[str]
    is_verified: bool
    
    class Config:
        from_attributes = True


class DoctorSearchResult(BaseModel):
    id: int
    user_id: int
    full_name: str
    specialization: str
    hospital_name: Optional[str]
    city: Optional[str]
    is_verified: bool
    connection_status: Optional[str] = None  # pending, accepted, none


class PatientSummary(BaseModel):
    patient_id: int
    patient_name: str
    latest_care_score: Optional[int]
    care_score_status: Optional[str]
    connection_status: str
    last_data_sync: Optional[datetime]


class PatientHealthSummary(BaseModel):
    patient_id: int
    patient_name: str
    age: Optional[int]
    gender: Optional[str]
    latest_care_score: Optional[int]
    care_score_status: Optional[str]
    avg_heart_rate_24h: Optional[float]
    avg_hrv_24h: Optional[float]
    last_bp_systolic: Optional[float]
    last_bp_diastolic: Optional[float]
    recent_anomalies: int
    trend_direction: str  # improving, stable, worsening
    health_suggestions: List[str]


# ==========================================
# Doctor Discovery APIs
# ==========================================

@router.get("/", response_model=List[DoctorSearchResult])
def list_doctors(
    specialization: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    verified_only: bool = Query(False),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """List all available doctors with optional filtering"""
    query = db.query(DoctorProfile).join(User).filter(User.is_active == True)
    
    if specialization:
        query = query.filter(DoctorProfile.specialization.ilike(f"%{specialization}%"))
    
    if city:
        query = query.filter(DoctorProfile.city.ilike(f"%{city}%"))
    
    if verified_only:
        query = query.filter(DoctorProfile.is_verified == True)
    
    doctors = query.offset(offset).limit(limit).all()
    
    return [
        DoctorSearchResult(
            id=doc.id,
            user_id=doc.user_id,
            full_name=doc.full_name,
            specialization=doc.specialization,
            hospital_name=doc.hospital_name,
            city=doc.city,
            is_verified=doc.is_verified
        )
        for doc in doctors
    ]


@router.get("/search")
def search_doctors(
    q: str = Query(..., min_length=2),
    patient_user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Search doctors by name, specialization, or hospital"""
    query = db.query(DoctorProfile).join(User).filter(User.is_active == True)
    
    # Search across multiple fields
    search_filter = (
        DoctorProfile.full_name.ilike(f"%{q}%") |
        DoctorProfile.specialization.ilike(f"%{q}%") |
        DoctorProfile.hospital_name.ilike(f"%{q}%") |
        DoctorProfile.city.ilike(f"%{q}%")
    )
    
    doctors = query.filter(search_filter).limit(20).all()
    
    results = []
    for doc in doctors:
        connection_status = None
        if patient_user_id:
            connection = db.query(PatientDoctor).filter(
                PatientDoctor.patient_id == patient_user_id,
                PatientDoctor.doctor_id == doc.user_id
            ).first()
            if connection:
                connection_status = connection.status
        
        results.append(DoctorSearchResult(
            id=doc.id,
            user_id=doc.user_id,
            full_name=doc.full_name,
            specialization=doc.specialization,
            hospital_name=doc.hospital_name,
            city=doc.city,
            is_verified=doc.is_verified,
            connection_status=connection_status
        ))
    
    return results


@router.get("/{doctor_id}", response_model=DoctorProfileResponse)
def get_doctor_profile(
    doctor_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed doctor profile"""
    doctor = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
    
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    return doctor


# ==========================================
# Doctor Dashboard APIs
# ==========================================

@router.get("/dashboard/patients/{doctor_user_id}", response_model=List[PatientSummary])
def get_doctor_patients(
    doctor_user_id: int,
    status: str = Query("accepted"),
    db: Session = Depends(get_db)
):
    """Get list of patients connected to this doctor"""
    # Verify doctor exists
    doctor = db.query(User).filter(User.id == doctor_user_id, User.role == "doctor").first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Get patient connections
    connections = db.query(PatientDoctor).filter(
        PatientDoctor.doctor_id == doctor_user_id,
        PatientDoctor.status == status
    ).all()
    
    patients = []
    for conn in connections:
        patient = db.query(User).filter(User.id == conn.patient_id).first()
        if not patient:
            continue
        
        # Get latest care score
        latest_score = db.query(CareScore).filter(
            CareScore.user_id == patient.id
        ).order_by(CareScore.timestamp.desc()).first()
        
        # Get last data sync
        last_data = db.query(HealthData).filter(
            HealthData.user_id == patient.id
        ).order_by(HealthData.timestamp.desc()).first()
        
        patients.append(PatientSummary(
            patient_id=patient.id,
            patient_name=patient.name,
            latest_care_score=latest_score.care_score if latest_score else None,
            care_score_status=latest_score.status if latest_score else None,
            connection_status=conn.status,
            last_data_sync=last_data.timestamp if last_data else None
        ))
    
    # Sort by care score (highest first for triage)
    patients.sort(key=lambda x: x.latest_care_score or 0, reverse=True)
    
    return patients


@router.get("/dashboard/patients/{doctor_user_id}/{patient_id}/health-summary")
def get_patient_health_summary(
    doctor_user_id: int,
    patient_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed health summary for a specific patient"""
    # Verify connection exists
    connection = db.query(PatientDoctor).filter(
        PatientDoctor.doctor_id == doctor_user_id,
        PatientDoctor.patient_id == patient_id,
        PatientDoctor.status == "accepted"
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
    
    # Get recent health data (last 24 hours)
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    recent_data = db.query(HealthData).filter(
        HealthData.user_id == patient_id,
        HealthData.timestamp >= cutoff
    ).all()
    
    # Calculate averages
    heart_rates = [d.heart_rate for d in recent_data if d.heart_rate]
    hrvs = [d.hrv for d in recent_data if d.hrv]
    
    avg_hr = sum(heart_rates) / len(heart_rates) if heart_rates else None
    avg_hrv = sum(hrvs) / len(hrvs) if hrvs else None
    
    # Get latest BP
    bp_data = db.query(HealthData).filter(
        HealthData.user_id == patient_id,
        HealthData.bp_systolic.isnot(None)
    ).order_by(HealthData.timestamp.desc()).first()
    
    # Count recent anomalies
    anomaly_count = db.query(HealthData).filter(
        HealthData.user_id == patient_id,
        HealthData.timestamp >= cutoff,
        HealthData.is_anomaly > 0
    ).count()
    
    # Determine trend
    trend = "stable"
    if latest_score:
        prev_scores = db.query(CareScore).filter(
            CareScore.user_id == patient_id
        ).order_by(CareScore.timestamp.desc()).limit(5).all()
        
        if len(prev_scores) >= 2:
            avg_recent = sum(s.care_score for s in prev_scores[:2]) / 2
            avg_older = sum(s.care_score for s in prev_scores[2:]) / len(prev_scores[2:]) if len(prev_scores) > 2 else avg_recent
            
            if avg_recent < avg_older - 10:
                trend = "improving"
            elif avg_recent > avg_older + 10:
                trend = "worsening"
                
    # Get health suggestions
    from app.services.notification_service import NotificationService
    notification_service = NotificationService(db)
    suggestions = notification_service.get_health_suggestions(
        latest_score.care_score if latest_score else 0
    )
    
    return {
        "patient_id": patient.id,
        "patient_name": patient.name,
        "age": patient.age,
        "gender": patient.gender,
        "latest_care_score": latest_score.care_score if latest_score else None,
        "care_score_status": latest_score.status if latest_score else None,
        "avg_heart_rate_24h": round(avg_hr, 1) if avg_hr else None,
        "avg_hrv_24h": round(avg_hrv, 1) if avg_hrv else None,
        "last_bp_systolic": bp_data.bp_systolic if bp_data else None,
        "last_bp_diastolic": bp_data.bp_diastolic if bp_data else None,
        "recent_anomalies": anomaly_count,
        "trend_direction": trend,
        "health_suggestions": suggestions
    }


@router.get("/dashboard/high-risk/{doctor_user_id}")
def get_high_risk_patients(
    doctor_user_id: int,
    threshold: int = Query(70),
    db: Session = Depends(get_db)
):
    """Get patients with high care scores requiring attention"""
    # Get connected patients
    connections = db.query(PatientDoctor).filter(
        PatientDoctor.doctor_id == doctor_user_id,
        PatientDoctor.status == "accepted"
    ).all()
    
    high_risk = []
    for conn in connections:
        latest_score = db.query(CareScore).filter(
            CareScore.user_id == conn.patient_id
        ).order_by(CareScore.timestamp.desc()).first()
        
        if latest_score and latest_score.care_score >= threshold:
            patient = db.query(User).filter(User.id == conn.patient_id).first()
            high_risk.append({
                "patient_id": patient.id,
                "patient_name": patient.name,
                "care_score": latest_score.care_score,
                "status": latest_score.status,
                "timestamp": latest_score.timestamp
            })
    
    # Sort by care score
    high_risk.sort(key=lambda x: x["care_score"], reverse=True)
    
    return high_risk


# ==========================================
# Doctor Profile Management
# ==========================================

@router.post("/profile/{user_id}", response_model=DoctorProfileResponse)
def create_doctor_profile(
    user_id: int,
    profile: DoctorProfileCreate,
    db: Session = Depends(get_db)
):
    """Create doctor profile for a user"""
    # Check user exists and is a doctor
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if profile already exists
    existing = db.query(DoctorProfile).filter(DoctorProfile.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Doctor profile already exists")
    
    # Update user role
    user.role = "doctor"
    
    # Create profile
    doctor_profile = DoctorProfile(
        user_id=user_id,
        **profile.dict()
    )
    
    db.add(doctor_profile)
    db.commit()
    db.refresh(doctor_profile)
    
    return doctor_profile


@router.put("/profile/{user_id}", response_model=DoctorProfileResponse)
def update_doctor_profile(
    user_id: int,
    profile: DoctorProfileCreate,
    db: Session = Depends(get_db)
):
    """Update existing doctor profile"""
    existing = db.query(DoctorProfile).filter(DoctorProfile.user_id == user_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Doctor profile not found")
    
    for key, value in profile.dict(exclude_unset=True).items():
        setattr(existing, key, value)
    
    existing.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(existing)
    
    return existing

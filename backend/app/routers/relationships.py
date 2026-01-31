"""
Relationships API Router for Pulse AI
Handles patient-doctor and patient-caretaker connections
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import secrets

from app.database import get_db
from app.models import User, PatientDoctor, PatientCaretaker, DoctorProfile, Notification

router = APIRouter(prefix="/relationships", tags=["Relationships"])


# ==========================================
# Pydantic Schemas
# ==========================================

class ConnectionRequest(BaseModel):
    notes: Optional[str] = None


class InviteCaretaker(BaseModel):
    caretaker_email: str
    access_level: str = "read"


class ConnectionResponse(BaseModel):
    id: int
    connection_type: str  # doctor, caretaker
    other_user_id: int
    other_user_name: str
    status: str
    created_at: datetime


# ==========================================
# Patient-Doctor Connection APIs
# ==========================================

@router.post("/patient/{patient_id}/connect-doctor/{doctor_user_id}")
def request_doctor_connection(
    patient_id: int,
    doctor_user_id: int,
    request: ConnectionRequest,
    db: Session = Depends(get_db)
):
    """Patient requests connection with a doctor"""
    # Verify patient exists
    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Verify doctor exists
    doctor = db.query(User).filter(User.id == doctor_user_id, User.role == "doctor").first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    # Check if connection already exists
    existing = db.query(PatientDoctor).filter(
        PatientDoctor.patient_id == patient_id,
        PatientDoctor.doctor_id == doctor_user_id
    ).first()
    
    if existing:
        if existing.status == "accepted":
            raise HTTPException(status_code=400, detail="Already connected to this doctor")
        elif existing.status == "pending":
            raise HTTPException(status_code=400, detail="Connection request already pending")
        # If rejected, allow re-request
        existing.status = "pending"
        existing.requested_at = datetime.utcnow()
        existing.patient_notes = request.notes
        db.commit()
        return {"status": "pending", "message": "Connection request sent"}
    
    # Create connection request
    connection = PatientDoctor(
        patient_id=patient_id,
        doctor_id=doctor_user_id,
        status="pending",
        requested_by="patient",
        patient_notes=request.notes
    )
    
    db.add(connection)
    
    # Create notification for doctor
    doctor_profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doctor_user_id).first()
    notification = Notification(
        user_id=doctor_user_id,
        notification_type="connection_request",
        title="New Patient Connection Request",
        message=f"{patient.name} wants to connect with you for health monitoring",
        related_user_id=patient_id,
        priority="normal"
    )
    
    db.add(notification)
    db.commit()
    
    return {"status": "pending", "message": "Connection request sent to doctor"}


@router.post("/doctor/{doctor_user_id}/respond/{connection_id}")
def doctor_respond_connection(
    doctor_user_id: int,
    connection_id: int,
    accept: bool,
    notes: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Doctor accepts or rejects patient connection request"""
    connection = db.query(PatientDoctor).filter(
        PatientDoctor.id == connection_id,
        PatientDoctor.doctor_id == doctor_user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    if connection.status != "pending":
        raise HTTPException(status_code=400, detail="Connection already processed")
    
    connection.status = "accepted" if accept else "rejected"
    connection.doctor_notes = notes
    if accept:
        connection.accepted_at = datetime.utcnow()
    
    # Notify patient
    patient = db.query(User).filter(User.id == connection.patient_id).first()
    doctor = db.query(User).filter(User.id == doctor_user_id).first()
    
    notification = Notification(
        user_id=connection.patient_id,
        notification_type="connection_response",
        title="Doctor Connection " + ("Accepted" if accept else "Declined"),
        message=f"Dr. {doctor.name} has {'accepted' if accept else 'declined'} your connection request",
        related_user_id=doctor_user_id,
        priority="normal"
    )
    
    db.add(notification)
    db.commit()
    
    return {"status": connection.status, "message": f"Connection {'accepted' if accept else 'rejected'}"}


# ==========================================
# Patient-Caretaker Connection APIs
# ==========================================

@router.post("/patient/{patient_id}/invite-caretaker")
def invite_caretaker(
    patient_id: int,
    invite: InviteCaretaker,
    db: Session = Depends(get_db)
):
    """Patient invites a caretaker by email"""
    # Verify patient exists
    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Find caretaker by email
    caretaker = db.query(User).filter(
        User.email == invite.caretaker_email,
        User.role == "caretaker"
    ).first()
    
    if not caretaker:
        # Generate invitation code for new caretaker
        invitation_code = secrets.token_urlsafe(16)
        # Store pending invitation
        return {
            "status": "invited",
            "message": f"Invitation sent to {invite.caretaker_email}",
            "invitation_code": invitation_code,
            "note": "Caretaker needs to register first"
        }
    
    # Check if connection already exists
    existing = db.query(PatientCaretaker).filter(
        PatientCaretaker.patient_id == patient_id,
        PatientCaretaker.caretaker_id == caretaker.id
    ).first()
    
    if existing:
        if existing.status == "accepted":
            raise HTTPException(status_code=400, detail="Already connected to this caretaker")
        elif existing.status == "pending":
            raise HTTPException(status_code=400, detail="Invitation already pending")
    
    # Create connection
    connection = PatientCaretaker(
        patient_id=patient_id,
        caretaker_id=caretaker.id,
        status="pending",
        access_level=invite.access_level
    )
    
    db.add(connection)
    
    # Create notification for caretaker
    notification = Notification(
        user_id=caretaker.id,
        notification_type="caretaker_invite",
        title="Patient Care Invitation",
        message=f"{patient.name} wants you to be their caretaker",
        related_user_id=patient_id,
        priority="normal"
    )
    
    db.add(notification)
    db.commit()
    
    return {"status": "pending", "message": "Invitation sent to caretaker"}


@router.post("/caretaker/{caretaker_user_id}/respond/{connection_id}")
def caretaker_respond_invitation(
    caretaker_user_id: int,
    connection_id: int,
    accept: bool,
    db: Session = Depends(get_db)
):
    """Caretaker accepts or rejects patient invitation"""
    connection = db.query(PatientCaretaker).filter(
        PatientCaretaker.id == connection_id,
        PatientCaretaker.caretaker_id == caretaker_user_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if connection.status != "pending":
        raise HTTPException(status_code=400, detail="Invitation already processed")
    
    connection.status = "accepted" if accept else "rejected"
    if accept:
        connection.accepted_at = datetime.utcnow()
    
    # Notify patient
    patient = db.query(User).filter(User.id == connection.patient_id).first()
    caretaker = db.query(User).filter(User.id == caretaker_user_id).first()
    
    notification = Notification(
        user_id=connection.patient_id,
        notification_type="caretaker_response",
        title="Caretaker Invitation " + ("Accepted" if accept else "Declined"),
        message=f"{caretaker.name} has {'accepted' if accept else 'declined'} your caretaker invitation",
        related_user_id=caretaker_user_id,
        priority="normal"
    )
    
    db.add(notification)
    db.commit()
    
    return {"status": connection.status, "message": f"Invitation {'accepted' if accept else 'rejected'}"}


# ==========================================
# Connection Management APIs
# ==========================================

@router.get("/patient/{patient_id}/connections")
def get_patient_connections(
    patient_id: int,
    db: Session = Depends(get_db)
):
    """Get all connections for a patient (doctors and caretakers)"""
    # Get doctor connections
    doctor_connections = db.query(PatientDoctor).filter(
        PatientDoctor.patient_id == patient_id
    ).all()
    
    # Get caretaker connections
    caretaker_connections = db.query(PatientCaretaker).filter(
        PatientCaretaker.patient_id == patient_id
    ).all()
    
    connections = []
    
    for conn in doctor_connections:
        doctor = db.query(User).filter(User.id == conn.doctor_id).first()
        doctor_profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == conn.doctor_id).first()
        connections.append({
            "id": conn.id,
            "connection_type": "doctor",
            "other_user_id": conn.doctor_id,
            "other_user_name": doctor.name if doctor else "Unknown",
            "specialization": doctor_profile.specialization if doctor_profile else None,
            "status": conn.status,
            "created_at": conn.requested_at
        })
    
    for conn in caretaker_connections:
        caretaker = db.query(User).filter(User.id == conn.caretaker_id).first()
        connections.append({
            "id": conn.id,
            "connection_type": "caretaker",
            "other_user_id": conn.caretaker_id,
            "other_user_name": caretaker.name if caretaker else "Unknown",
            "access_level": conn.access_level,
            "status": conn.status,
            "created_at": conn.invited_at
        })
    
    return connections


@router.delete("/patient/{patient_id}/doctor/{connection_id}")
def remove_doctor_connection(
    patient_id: int,
    connection_id: int,
    db: Session = Depends(get_db)
):
    """Patient removes a doctor connection"""
    connection = db.query(PatientDoctor).filter(
        PatientDoctor.id == connection_id,
        PatientDoctor.patient_id == patient_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    db.delete(connection)
    db.commit()
    
    return {"message": "Doctor connection removed"}


@router.delete("/patient/{patient_id}/caretaker/{connection_id}")
def remove_caretaker_connection(
    patient_id: int,
    connection_id: int,
    db: Session = Depends(get_db)
):
    """Patient removes a caretaker connection"""
    connection = db.query(PatientCaretaker).filter(
        PatientCaretaker.id == connection_id,
        PatientCaretaker.patient_id == patient_id
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    db.delete(connection)
    db.commit()
    
    return {"message": "Caretaker connection removed"}


# ==========================================
# Pending Requests APIs
# ==========================================

@router.get("/doctor/{doctor_user_id}/pending")
def get_doctor_pending_requests(
    doctor_user_id: int,
    db: Session = Depends(get_db)
):
    """Get pending patient connection requests for a doctor"""
    pending = db.query(PatientDoctor).filter(
        PatientDoctor.doctor_id == doctor_user_id,
        PatientDoctor.status == "pending"
    ).all()
    
    return [
        {
            "id": conn.id,
            "patient_id": conn.patient_id,
            "patient_name": db.query(User).filter(User.id == conn.patient_id).first().name,
            "notes": conn.patient_notes,
            "requested_at": conn.requested_at
        }
        for conn in pending
    ]


@router.get("/caretaker/{caretaker_user_id}/pending")
def get_caretaker_pending_invitations(
    caretaker_user_id: int,
    db: Session = Depends(get_db)
):
    """Get pending patient invitations for a caretaker"""
    pending = db.query(PatientCaretaker).filter(
        PatientCaretaker.caretaker_id == caretaker_user_id,
        PatientCaretaker.status == "pending"
    ).all()
    
    return [
        {
            "id": conn.id,
            "patient_id": conn.patient_id,
            "patient_name": db.query(User).filter(User.id == conn.patient_id).first().name,
            "access_level": conn.access_level,
            "invited_at": conn.invited_at
        }
        for conn in pending
    ]

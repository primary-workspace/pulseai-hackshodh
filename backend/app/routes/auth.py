"""
Authentication Routes for Pulse AI
API key management and device registration
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================
# Pydantic Models
# ============================================

class GenerateAPIKeyRequest(BaseModel):
    user_id: int
    name: Optional[str] = None
    device_id: Optional[str] = None
    expires_in_days: Optional[int] = None


class RegisterDeviceRequest(BaseModel):
    user_id: int
    device_id: str
    device_name: Optional[str] = None
    device_type: str = "android"


class APIKeyResponse(BaseModel):
    id: int
    user_id: int
    name: Optional[str]
    device_id: Optional[str]
    created_at: str
    last_used_at: Optional[str]
    expires_at: Optional[str]
    is_active: bool
    request_count: int


class DeviceResponse(BaseModel):
    id: int
    user_id: int
    device_id: str
    device_name: Optional[str]
    device_type: Optional[str]
    registered_at: str
    last_sync_at: Optional[str]
    is_active: bool


# ============================================
# API Key Endpoints
# ============================================

@router.post("/api-keys/generate")
async def generate_api_key(
    request: GenerateAPIKeyRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a new API key for a user
    
    The raw key is returned ONLY ONCE - save it securely!
    """
    try:
        auth_service = AuthService(db)
        raw_key, api_key = auth_service.generate_api_key(
            user_id=request.user_id,
            name=request.name,
            device_id=request.device_id,
            expires_in_days=request.expires_in_days
        )
        
        return {
            "success": True,
            "api_key": raw_key,
            "key_id": api_key.id,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "warning": "Save this API key securely - it cannot be retrieved again!"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/api-keys/{user_id}")
async def list_api_keys(
    user_id: int,
    db: Session = Depends(get_db)
):
    """List all API keys for a user (keys are masked)"""
    auth_service = AuthService(db)
    keys = auth_service.get_user_api_keys(user_id)
    
    return {
        "user_id": user_id,
        "api_keys": [
            {
                "id": key.id,
                "name": key.name,
                "device_id": key.device_id,
                "created_at": key.created_at.isoformat(),
                "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "is_active": key.is_active,
                "request_count": key.request_count
            }
            for key in keys
        ]
    }


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: int,
    db: Session = Depends(get_db)
):
    """Revoke an API key"""
    auth_service = AuthService(db)
    success = auth_service.revoke_api_key(key_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    
    return {"success": True, "message": "API key revoked"}


@router.get("/validate")
async def validate_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db)
):
    """Validate an API key and return user info"""
    auth_service = AuthService(db)
    user = auth_service.validate_api_key(x_api_key)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired API key")
    
    return {
        "valid": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        }
    }


# ============================================
# Device Registration Endpoints
# ============================================

@router.post("/devices/register")
async def register_device(
    request: RegisterDeviceRequest,
    db: Session = Depends(get_db)
):
    """Register a new device for a user"""
    try:
        auth_service = AuthService(db)
        device = auth_service.register_device(
            user_id=request.user_id,
            device_id=request.device_id,
            device_name=request.device_name,
            device_type=request.device_type
        )
        
        return {
            "success": True,
            "device": {
                "id": device.id,
                "device_id": device.device_id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "registered_at": device.registered_at.isoformat()
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/devices/{user_id}")
async def list_devices(
    user_id: int,
    db: Session = Depends(get_db)
):
    """List all registered devices for a user"""
    auth_service = AuthService(db)
    devices = auth_service.get_user_devices(user_id)
    
    return {
        "user_id": user_id,
        "devices": [
            {
                "id": device.id,
                "device_id": device.device_id,
                "device_name": device.device_name,
                "device_type": device.device_type,
                "registered_at": device.registered_at.isoformat(),
                "last_sync_at": device.last_sync_at.isoformat() if device.last_sync_at else None,
                "is_active": device.is_active
            }
            for device in devices
        ]
    }


# ============================================
# Onboarding Flow
# ============================================

@router.post("/onboard")
async def onboard_user(
    email: str,
    name: str,
    device_id: Optional[str] = None,
    device_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Complete onboarding flow:
    1. Create or get user
    2. Generate API key
    3. Register device (if provided)
    
    Returns everything needed for the Android app
    """
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create new user
        user = User(
            email=email,
            name=name,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Generate API key
    auth_service = AuthService(db)
    raw_key, api_key = auth_service.generate_api_key(
        user_id=user.id,
        name=f"Key for {device_name or 'device'}",
        device_id=device_id
    )
    
    # Register device if provided
    device = None
    if device_id:
        device = auth_service.register_device(
            user_id=user.id,
            device_id=device_id,
            device_name=device_name,
            device_type="android"
        )
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name
        },
        "api_key": raw_key,
        "device": {
            "id": device.id if device else None,
            "device_id": device_id
        } if device else None,
        "webhook_config": {
            "endpoint": "/webhook/ingest",
            "batch_endpoint": "/webhook/ingest-batch",
            "analyze_endpoint": "/webhook/ingest-and-analyze",
            "headers": {
                "X-API-Key": raw_key,
                "X-Device-ID": device_id or ""
            }
        }
    }


# ============================================
# Role-Based Registration
# ============================================

class PatientRegisterRequest(BaseModel):
    email: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    phone: Optional[str] = None


class DoctorRegisterRequest(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None
    # Doctor profile fields
    full_name: str
    specialization: str
    qualification: Optional[str] = None
    hospital_name: Optional[str] = None
    hospital_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    emergency_contact: Optional[str] = None
    license_number: Optional[str] = None


class CaretakerRegisterRequest(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None
    # Caretaker profile fields
    full_name: str
    relationship_type: Optional[str] = None
    phone_number: Optional[str] = None


@router.post("/register/patient")
async def register_patient(
    request: PatientRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new patient user"""
    # Check if user already exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=request.email,
        name=request.name,
        age=request.age,
        gender=request.gender,
        phone=request.phone,
        role="patient",
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        },
        "redirect": "/dashboard"
    }


@router.post("/register/doctor")
async def register_doctor(
    request: DoctorRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new doctor with extended profile"""
    from app.models.doctor_profile import DoctorProfile
    
    # Check if user already exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=request.email,
        name=request.name,
        phone=request.phone,
        role="doctor",
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create doctor profile
    doctor_profile = DoctorProfile(
        user_id=user.id,
        full_name=request.full_name,
        specialization=request.specialization,
        qualification=request.qualification,
        hospital_name=request.hospital_name,
        hospital_address=request.hospital_address,
        city=request.city,
        state=request.state,
        country=request.country,
        emergency_contact=request.emergency_contact,
        license_number=request.license_number
    )
    
    db.add(doctor_profile)
    db.commit()
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        },
        "doctor_profile_id": doctor_profile.id,
        "redirect": "/doctor-dashboard"
    }


@router.post("/register/caretaker")
async def register_caretaker(
    request: CaretakerRegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new caretaker user"""
    from app.models.caretaker_profile import CaretakerProfile
    
    # Check if user already exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=request.email,
        name=request.name,
        phone=request.phone,
        role="caretaker",
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create caretaker profile
    caretaker_profile = CaretakerProfile(
        user_id=user.id,
        full_name=request.full_name,
        relationship_type=request.relationship_type,
        phone_number=request.phone_number or request.phone
    )
    
    db.add(caretaker_profile)
    db.commit()
    
    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role
        },
        "caretaker_profile_id": caretaker_profile.id,
        "redirect": "/caretaker-dashboard"
    }


@router.get("/user/{user_id}/role")
async def get_user_role(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user role and profile info"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    response = {
        "user_id": user.id,
        "role": user.role or "patient",
        "name": user.name,
        "email": user.email
    }
    
    # Add role-specific profile
    if user.role == "doctor":
        from app.models.doctor_profile import DoctorProfile
        profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == user_id).first()
        if profile:
            response["doctor_profile"] = {
                "id": profile.id,
                "specialization": profile.specialization,
                "hospital_name": profile.hospital_name,
                "is_verified": profile.is_verified
            }
    elif user.role == "caretaker":
        from app.models.caretaker_profile import CaretakerProfile
        profile = db.query(CaretakerProfile).filter(CaretakerProfile.user_id == user_id).first()
        if profile:
            response["caretaker_profile"] = {
                "id": profile.id,
                "relationship_type": profile.relationship_type
            }
    
    return response

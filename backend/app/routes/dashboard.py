"""
Dashboard Routes for Pulse AI
API endpoints for frontend dashboard data
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.user import User
from app.models.health_data import HealthData
from app.models.care_score import CareScore, Escalation
from app.services.auth_service import AuthService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ============================================
# Dashboard Summary Endpoint
# ============================================

@router.get("/summary/{user_id}")
async def get_dashboard_summary(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get complete dashboard summary for a user
    Returns: CareScore, latest metrics, trends, and active escalations
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get latest CareScore
    latest_score = db.query(CareScore).filter(
        CareScore.user_id == user_id
    ).order_by(CareScore.timestamp.desc()).first()
    
    # Get latest health data
    latest_health = db.query(HealthData).filter(
        HealthData.user_id == user_id
    ).order_by(HealthData.timestamp.desc()).first()
    
    # Get active escalations (acknowledged is INTEGER: 0=not acknowledged)
    active_escalations = db.query(Escalation).filter(
        Escalation.user_id == user_id,
        Escalation.acknowledged == 0
    ).order_by(Escalation.timestamp.desc()).all()
    
    # Get CareScore history (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    score_history = db.query(CareScore).filter(
        CareScore.user_id == user_id,
        CareScore.timestamp >= seven_days_ago
    ).order_by(CareScore.timestamp.asc()).all()
    
    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email
        },
        "care_score": {
            "score": latest_score.care_score if latest_score else None,
            "status": latest_score.status if latest_score else "unknown",
            "components": {
                "severity": latest_score.severity_score if latest_score else 0,
                "persistence": latest_score.persistence_score if latest_score else 0,
                "cross_signal": latest_score.cross_signal_score if latest_score else 0,
                "manual_modifier": latest_score.manual_modifier_score if latest_score else 0
            },
            "drift_score": latest_score.drift_score if latest_score else 0,
            "confidence": latest_score.confidence_score if latest_score else 0,
            "stability": latest_score.stability_score if latest_score else 0,
            "explanation": latest_score.explanation if latest_score else None,
            "updated_at": latest_score.timestamp.isoformat() if latest_score else None
        } if latest_score else None,
        "current_metrics": {
            "heart_rate": {
                "value": latest_health.heart_rate if latest_health else None,
                "baseline": user.baseline_heart_rate,
                "unit": "bpm"
            },
            "hrv": {
                "value": latest_health.hrv if latest_health else None,
                "baseline": user.baseline_hrv,
                "unit": "ms"
            },
            "sleep_duration": {
                "value": latest_health.sleep_duration if latest_health else None,
                "baseline": user.baseline_sleep_hours,
                "unit": "hours"
            },
            "activity_level": {
                "value": latest_health.activity_level if latest_health else None,
                "baseline": user.baseline_activity_level,
                "unit": "steps"
            },
            "breathing_rate": {
                "value": latest_health.breathing_rate if latest_health else None,
                "baseline": user.baseline_breathing_rate,
                "unit": "breaths/min"
            },
            "bp_systolic": {
                "value": latest_health.bp_systolic if latest_health else None,
                "baseline": user.baseline_bp_systolic,
                "unit": "mmHg"
            },
            "bp_diastolic": {
                "value": latest_health.bp_diastolic if latest_health else None,
                "baseline": user.baseline_bp_diastolic,
                "unit": "mmHg"
            },
            "blood_sugar": {
                "value": latest_health.blood_sugar if latest_health else None,
                "baseline": user.baseline_blood_sugar,
                "unit": "mg/dL"
            },
            "updated_at": latest_health.timestamp.isoformat() if latest_health else None
        } if latest_health else None,
        "escalations": [
            {
                "id": e.id,
                "level": e.level,
                "title": f"Level {e.level} Alert",
                "message": e.message,
                "timestamp": e.timestamp.isoformat(),
                "acknowledged": e.acknowledged
            }
            for e in active_escalations
        ],
        "score_trend": [
            {
                "date": s.timestamp.strftime("%b %d"),
                "score": s.care_score,
                "status": s.status
            }
            for s in score_history
        ]
    }


# ============================================
# Health Metrics Trends
# ============================================

@router.get("/trends/{user_id}")
async def get_health_trends(
    user_id: int,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get health data trends for specified number of days"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    health_data = db.query(HealthData).filter(
        HealthData.user_id == user_id,
        HealthData.timestamp >= start_date
    ).order_by(HealthData.timestamp.asc()).all()
    
    # Aggregate by day
    daily_data = {}
    for record in health_data:
        date_key = record.timestamp.strftime("%Y-%m-%d")
        if date_key not in daily_data:
            daily_data[date_key] = {
                "date": date_key,
                "heart_rate": [],
                "hrv": [],
                "sleep_duration": [],
                "activity_level": [],
                "breathing_rate": []
            }
        
        if record.heart_rate:
            daily_data[date_key]["heart_rate"].append(record.heart_rate)
        if record.hrv:
            daily_data[date_key]["hrv"].append(record.hrv)
        if record.sleep_duration:
            daily_data[date_key]["sleep_duration"].append(record.sleep_duration)
        if record.activity_level:
            daily_data[date_key]["activity_level"].append(record.activity_level)
        if record.breathing_rate:
            daily_data[date_key]["breathing_rate"].append(record.breathing_rate)
    
    # Calculate daily averages
    trend_data = []
    for date_key in sorted(daily_data.keys()):
        day = daily_data[date_key]
        trend_data.append({
            "date": date_key,
            "heart_rate": sum(day["heart_rate"]) / len(day["heart_rate"]) if day["heart_rate"] else None,
            "hrv": sum(day["hrv"]) / len(day["hrv"]) if day["hrv"] else None,
            "sleep_duration": sum(day["sleep_duration"]) / len(day["sleep_duration"]) if day["sleep_duration"] else None,
            "activity_level": sum(day["activity_level"]) / len(day["activity_level"]) if day["activity_level"] else None,
            "breathing_rate": sum(day["breathing_rate"]) / len(day["breathing_rate"]) if day["breathing_rate"] else None
        })
    
    return {
        "user_id": user_id,
        "days": days,
        "trends": trend_data,
        "baselines": {
            "heart_rate": user.baseline_heart_rate,
            "hrv": user.baseline_hrv,
            "sleep_duration": user.baseline_sleep_hours,
            "activity_level": user.baseline_activity_level,
            "breathing_rate": user.baseline_breathing_rate
        }
    }


# ============================================
# CareScore History
# ============================================

@router.get("/carescore-history/{user_id}")
async def get_carescore_history(
    user_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get CareScore history for specified number of days"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    scores = db.query(CareScore).filter(
        CareScore.user_id == user_id,
        CareScore.timestamp >= start_date
    ).order_by(CareScore.timestamp.asc()).all()
    
    return {
        "user_id": user_id,
        "days": days,
        "history": [
            {
                "id": s.id,
                "timestamp": s.timestamp.isoformat(),
                "date": s.timestamp.strftime("%b %d"),
                "score": s.care_score,
                "status": s.status,
                "components": {
                    "severity": s.severity_score,
                    "persistence": s.persistence_score,
                    "cross_signal": s.cross_signal_score,
                    "manual_modifier": s.manual_modifier_score
                },
                "drift_score": s.drift_score,
                "confidence": s.confidence_score
            }
            for s in scores
        ]
    }


# ============================================
# Insights
# ============================================

@router.get("/insights/{user_id}")
async def get_insights(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get AI-generated insights for a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get latest health data
    latest_health = db.query(HealthData).filter(
        HealthData.user_id == user_id
    ).order_by(HealthData.timestamp.desc()).first()
    
    if not latest_health:
        return {"user_id": user_id, "insights": []}
    
    insights = []
    
    # Compare current values to baselines
    if latest_health.heart_rate and user.baseline_heart_rate:
        diff = latest_health.heart_rate - user.baseline_heart_rate
        pct = (diff / user.baseline_heart_rate) * 100
        if abs(pct) > 10:
            insights.append({
                "type": "warning" if pct > 10 else "info",
                "metric": "Heart Rate",
                "title": f"Heart Rate {'Elevated' if pct > 0 else 'Lower'}",
                "description": f"Your heart rate is {abs(pct):.0f}% {'higher' if pct > 0 else 'lower'} than your baseline.",
                "current": latest_health.heart_rate,
                "baseline": user.baseline_heart_rate,
                "recommendation": "Monitor for persistence. Consider consulting a doctor if this continues."
            })
    
    if latest_health.hrv and user.baseline_hrv:
        diff = latest_health.hrv - user.baseline_hrv
        pct = (diff / user.baseline_hrv) * 100
        if pct < -15:  # HRV decrease is concerning
            insights.append({
                "type": "warning",
                "metric": "HRV",
                "title": "HRV Decreased",
                "description": f"Your heart rate variability is {abs(pct):.0f}% lower than usual.",
                "current": latest_health.hrv,
                "baseline": user.baseline_hrv,
                "recommendation": "Lower HRV may indicate stress or fatigue. Consider rest and relaxation."
            })
    
    if latest_health.sleep_duration and user.baseline_sleep_hours:
        diff = latest_health.sleep_duration - user.baseline_sleep_hours
        pct = (diff / user.baseline_sleep_hours) * 100
        if pct < -20:
            insights.append({
                "type": "warning",
                "metric": "Sleep",
                "title": "Sleep Duration Declining",
                "description": f"Your sleep is {abs(pct):.0f}% shorter than your usual pattern.",
                "current": latest_health.sleep_duration,
                "baseline": user.baseline_sleep_hours,
                "recommendation": "Try to maintain a consistent sleep schedule."
            })
    
    if latest_health.activity_level and user.baseline_activity_level:
        diff = latest_health.activity_level - user.baseline_activity_level
        pct = (diff / user.baseline_activity_level) * 100
        if pct > 10:
            insights.append({
                "type": "success",
                "metric": "Activity",
                "title": "Activity Levels Up",
                "description": f"Your activity is {pct:.0f}% higher than usual.",
                "current": latest_health.activity_level,
                "baseline": user.baseline_activity_level,
                "recommendation": "Great job staying active!"
            })
        elif pct < -25:
            insights.append({
                "type": "info",
                "metric": "Activity",
                "title": "Activity Levels Lower",
                "description": f"Your activity is {abs(pct):.0f}% lower than usual.",
                "current": latest_health.activity_level,
                "baseline": user.baseline_activity_level,
                "recommendation": "Try to incorporate some physical activity into your day."
            })
    
    return {
        "user_id": user_id,
        "insights": insights,
        "updated_at": latest_health.timestamp.isoformat()
    }


# ============================================
# Escalation Management
# ============================================

@router.get("/escalations/{user_id}")
async def get_user_escalations(
    user_id: int,
    include_acknowledged: bool = False,
    db: Session = Depends(get_db)
):
    """Get all escalations for a user"""
    query = db.query(Escalation).filter(Escalation.user_id == user_id)
    
    if not include_acknowledged:
        query = query.filter(Escalation.acknowledged == 0)
    
    escalations = query.order_by(Escalation.timestamp.desc()).all()
    
    return {
        "user_id": user_id,
        "active_count": len([e for e in escalations if e.acknowledged == 0]),
        "escalations": [
            {
                "id": e.id,
                "level": e.level,
                "message": e.message,
                "timestamp": e.timestamp.isoformat(),
                "acknowledged": e.acknowledged,
                "acknowledged_at": e.acknowledged_at.isoformat() if e.acknowledged_at else None,
                "action_taken": e.action_taken
            }
            for e in escalations
        ]
    }


@router.post("/escalations/{escalation_id}/acknowledge")
async def acknowledge_escalation(
    escalation_id: int,
    action: str = "dismissed",
    db: Session = Depends(get_db)
):
    """Acknowledge an escalation"""
    escalation = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    
    if not escalation:
        raise HTTPException(status_code=404, detail="Escalation not found")
    
    escalation.acknowledged = True
    escalation.acknowledged_at = datetime.utcnow()
    escalation.action_taken = action
    db.commit()
    
    return {
        "success": True,
        "escalation_id": escalation_id,
        "action": action
    }

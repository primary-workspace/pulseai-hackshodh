"""
Notification Service for Pulse AI
Handles creating and distributing notifications when anomalies are detected
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional

from app.models import (
    User, Notification, CareScore, 
    PatientDoctor, PatientCaretaker
)


class NotificationService:
    """Service for creating and managing notifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_notification(
        self,
        user_id: int,
        notification_type: str,
        title: str,
        message: str = None,
        related_user_id: int = None,
        related_care_score_id: int = None,
        priority: str = "normal"
    ) -> Notification:
        """Create a single notification"""
        notification = Notification(
            user_id=user_id,
            notification_type=notification_type,
            title=title,
            message=message,
            related_user_id=related_user_id,
            related_care_score_id=related_care_score_id,
            priority=priority
        )
        
        self.db.add(notification)
        return notification
    
    def notify_anomaly_detected(
        self,
        patient_id: int,
        care_score: CareScore,
        anomaly_details: str = None
    ) -> List[int]:
        """
        Notify patient, doctors, and caretakers about an anomaly.
        Returns list of notified user IDs.
        """
        notified_users = []
        
        patient = self.db.query(User).filter(User.id == patient_id).first()
        if not patient:
            return notified_users
        
        # Determine priority based on care score
        if care_score.care_score >= 70:
            priority = "critical"
            severity = "High Risk"
        elif care_score.care_score >= 50:
            priority = "high"
            severity = "Moderate Concern"
        else:
            priority = "normal"
            severity = "Mild Concern"
        
        # 1. Notify patient
        patient_notification = self.create_notification(
            user_id=patient_id,
            notification_type="anomaly",
            title=f"Health Alert: {severity}",
            message=f"Your CareScore has reached {care_score.care_score}. {anomaly_details or ''}",
            related_care_score_id=care_score.id,
            priority=priority
        )
        notified_users.append(patient_id)
        
        # 2. Notify all linked doctors
        doctor_connections = self.db.query(PatientDoctor).filter(
            PatientDoctor.patient_id == patient_id,
            PatientDoctor.status == "accepted"
        ).all()
        
        for conn in doctor_connections:
            self.create_notification(
                user_id=conn.doctor_id,
                notification_type="patient_anomaly",
                title=f"Patient Alert: {patient.name}",
                message=f"CareScore: {care_score.care_score} ({severity}). {anomaly_details or ''}",
                related_user_id=patient_id,
                related_care_score_id=care_score.id,
                priority=priority
            )
            notified_users.append(conn.doctor_id)
        
        # 3. Notify all linked caretakers
        caretaker_connections = self.db.query(PatientCaretaker).filter(
            PatientCaretaker.patient_id == patient_id,
            PatientCaretaker.status == "accepted"
        ).all()
        
        for conn in caretaker_connections:
            # Simplified message for caretakers
            caretaker_message = f"{patient.name}'s health status requires attention. ({severity})"
            
            self.create_notification(
                user_id=conn.caretaker_id,
                notification_type="patient_alert",
                title=f"Alert: {patient.name}",
                message=caretaker_message,
                related_user_id=patient_id,
                related_care_score_id=care_score.id,
                priority=priority
            )
            notified_users.append(conn.caretaker_id)
        
        # Commit all notifications
        self.db.commit()
        
        return notified_users
    
    def notify_care_score_threshold(
        self,
        patient_id: int,
        care_score: CareScore,
        threshold: int
    ) -> List[int]:
        """
        Notify when care score crosses a threshold.
        """
        notified_users = []
        
        patient = self.db.query(User).filter(User.id == patient_id).first()
        if not patient:
            return notified_users
        
        if care_score.care_score >= threshold:
            return self.notify_anomaly_detected(
                patient_id=patient_id,
                care_score=care_score,
                anomaly_details=f"Care score has crossed the {threshold} threshold."
            )
        
        return notified_users
    
    def notify_sustained_drift(
        self,
        patient_id: int,
        care_score: CareScore,
        drift_count: int
    ) -> List[int]:
        """
        Notify when patient shows sustained drift (multiple consecutive anomalies).
        """
        return self.notify_anomaly_detected(
            patient_id=patient_id,
            care_score=care_score,
            anomaly_details=f"Sustained health drift detected ({drift_count} consecutive readings)."
        )
    
    def send_connection_notification(
        self,
        to_user_id: int,
        from_user_id: int,
        connection_type: str,  # doctor_request, caretaker_invite
        action: str  # request, accept, reject
    ):
        """Send notification about connection status changes"""
        from_user = self.db.query(User).filter(User.id == from_user_id).first()
        if not from_user:
            return
        
        if connection_type == "doctor_request":
            if action == "request":
                title = "New Patient Connection Request"
                message = f"{from_user.name} wants to connect with you"
            elif action == "accept":
                title = "Doctor Connection Accepted"
                message = f"Dr. {from_user.name} has accepted your connection request"
            else:
                title = "Doctor Connection Declined"
                message = f"Your connection request was declined"
        else:  # caretaker_invite
            if action == "request":
                title = "Caretaker Invitation"
                message = f"{from_user.name} wants you to be their caretaker"
            elif action == "accept":
                title = "Caretaker Invitation Accepted"
                message = f"{from_user.name} has accepted your invitation"
            else:
                title = "Caretaker Invitation Declined"
                message = f"Your caretaker invitation was declined"
        
        self.create_notification(
            user_id=to_user_id,
            notification_type=connection_type,
            title=title,
            message=message,
            related_user_id=from_user_id,
            priority="normal"
        )
        
        self.db.commit()


def get_health_suggestions(care_score: CareScore, patient: User) -> List[str]:
    """
    Generate non-clinical lifestyle suggestions based on CareScore.
    These are NOT medical advice - just general wellness tips.
    """
    suggestions = []
    
    # Only show suggestions when there's an anomaly
    if care_score.care_score < 25:
        return []
    
    # Parse explanation for component insights
    explanation = care_score.explanation or ""
    
    # Sleep-related suggestions
    if "sleep" in explanation.lower() or care_score.care_score >= 50:
        suggestions.append("Consider maintaining a consistent sleep schedule")
        suggestions.append("Avoid screens 1 hour before bedtime")
    
    # Heart rate / stress suggestions
    if "heart" in explanation.lower() or "hr" in explanation.lower():
        suggestions.append("Try light relaxation exercises or deep breathing")
        suggestions.append("Consider a short walk outdoors")
    
    # Activity suggestions
    if "activity" in explanation.lower() or care_score.care_score >= 40:
        suggestions.append("Gentle physical activity may help - even a 10-minute walk")
    
    # Hydration
    if care_score.care_score >= 30:
        suggestions.append("Stay well hydrated throughout the day")
    
    # Blood pressure related
    if "bp" in explanation.lower() or "pressure" in explanation.lower():
        suggestions.append("Consider moderating salt intake")
        suggestions.append("Practice stress-relief techniques")
    
    # General high score suggestions
    if care_score.care_score >= 70:
        suggestions.append("Consider contacting your healthcare provider")
        suggestions.append("Rest and monitor how you feel")
    
    # Limit to 4 suggestions max
    return suggestions[:4]

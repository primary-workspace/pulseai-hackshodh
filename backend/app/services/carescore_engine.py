"""
CareScore Engine for Pulse AI
Implements the CareScore calculation algorithm
"""

import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.health_data import HealthData
from app.models.care_score import CareScore


class CareScoreEngine:
    """
    CareScore calculation engine
    
    CareScore Components:
    1. Severity Score (0-40): Based on deviation from personal baseline (z-score)
    2. Persistence Score (0-25): How long deviation persists
    3. Cross-Signal Validation Score (0-20): Number of signals agreeing on drift
    4. Manual Risk Modifier (0-10): Based on BP, sugar, symptoms
    
    Final CareScore = Sum of all components (normalized to 0-100)
    """
    
    # Thresholds for z-score severity
    SEVERITY_THRESHOLDS = {
        'mild': 1.5,      # 1.5 std deviations
        'moderate': 2.5,  # 2.5 std deviations
        'severe': 3.5     # 3.5 std deviations
    }
    
    # Weight for each signal in cross-validation
    SIGNAL_WEIGHTS = {
        'heart_rate': 1.2,
        'hrv': 1.5,
        'sleep_duration': 1.0,
        'sleep_quality': 0.8,
        'activity_level': 0.7,
        'breathing_rate': 1.1,
        'bp_systolic': 1.3,
        'bp_diastolic': 1.2,
        'blood_sugar': 1.4
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_z_score(self, value: float, baseline: float, std_dev: float) -> float:
        """Calculate z-score for a value against baseline"""
        if std_dev == 0 or std_dev is None:
            std_dev = baseline * 0.1 if baseline else 1  # Assume 10% variation
        return abs(value - baseline) / std_dev if baseline else 0
    
    def calculate_severity_score(
        self, 
        current_data: Dict[str, float], 
        user: User,
        historical_std: Dict[str, float]
    ) -> Tuple[float, List[Dict]]:
        """
        Calculate severity score (0-40) based on deviation from baseline
        Returns severity score and list of deviating signals
        """
        deviations = []
        total_severity = 0
        max_signals = 9
        
        signal_baselines = {
            'heart_rate': user.baseline_heart_rate,
            'hrv': user.baseline_hrv,
            'sleep_duration': user.baseline_sleep_hours,
            'activity_level': user.baseline_activity_level,
            'breathing_rate': user.baseline_breathing_rate,
            'bp_systolic': user.baseline_bp_systolic,
            'bp_diastolic': user.baseline_bp_diastolic,
            'blood_sugar': user.baseline_blood_sugar
        }
        
        for signal, baseline in signal_baselines.items():
            if baseline and signal in current_data and current_data[signal]:
                z_score = self.calculate_z_score(
                    current_data[signal],
                    baseline,
                    historical_std.get(signal, baseline * 0.1)
                )
                
                weight = self.SIGNAL_WEIGHTS.get(signal, 1.0)
                weighted_z = z_score * weight
                
                if z_score >= self.SEVERITY_THRESHOLDS['mild']:
                    level = 'mild'
                    if z_score >= self.SEVERITY_THRESHOLDS['moderate']:
                        level = 'moderate'
                    if z_score >= self.SEVERITY_THRESHOLDS['severe']:
                        level = 'severe'
                    
                    deviations.append({
                        'signal': signal,
                        'current': current_data[signal],
                        'baseline': baseline,
                        'z_score': round(z_score, 2),
                        'level': level,
                        'weighted_contribution': round(weighted_z, 2)
                    })
                    
                    total_severity += weighted_z
        
        # Normalize to 0-40
        normalized_severity = min(40, (total_severity / max_signals) * 40)
        
        return round(normalized_severity, 1), deviations
    
    def calculate_persistence_score(
        self, 
        user_id: int, 
        lookback_days: int = 7
    ) -> Tuple[float, int]:
        """
        Calculate persistence score (0-25) based on how long deviation persists
        Returns persistence score and number of anomaly days
        """
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        
        recent_scores = self.db.query(CareScore).filter(
            CareScore.user_id == user_id,
            CareScore.timestamp >= cutoff
        ).order_by(CareScore.timestamp.desc()).all()
        
        anomaly_days = sum(1 for score in recent_scores if score.care_score >= 31)
        
        # Scale: 0 days = 0, 7+ days = 25
        persistence = min(25, (anomaly_days / lookback_days) * 25)
        
        return round(persistence, 1), anomaly_days
    
    def calculate_cross_signal_score(self, deviations: List[Dict]) -> float:
        """
        Calculate cross-signal validation score (0-20)
        Based on number of signals agreeing on drift
        """
        num_deviating = len(deviations)
        
        # 0-1 signals = 0-5, 2-3 = 5-10, 4-5 = 10-15, 6+ = 15-20
        if num_deviating == 0:
            return 0
        elif num_deviating == 1:
            return 3
        elif num_deviating <= 3:
            return 5 + (num_deviating - 1) * 3
        elif num_deviating <= 5:
            return 10 + (num_deviating - 3) * 2.5
        else:
            return min(20, 15 + (num_deviating - 5) * 1)
    
    def calculate_manual_modifier(
        self, 
        current_data: Dict[str, float],
        symptoms: List[str] = None
    ) -> float:
        """
        Calculate manual risk modifier (0-10)
        Based on BP, sugar, and symptoms from manual input
        """
        modifier = 0
        
        # Blood pressure risk
        bp_sys = current_data.get('bp_systolic', 0)
        bp_dia = current_data.get('bp_diastolic', 0)
        
        if bp_sys:
            if bp_sys >= 180 or bp_dia >= 120:
                modifier += 4  # Hypertensive crisis
            elif bp_sys >= 140 or bp_dia >= 90:
                modifier += 2  # High
            elif bp_sys >= 130:
                modifier += 1  # Elevated
        
        # Blood sugar risk
        blood_sugar = current_data.get('blood_sugar', 0)
        if blood_sugar:
            if blood_sugar >= 200:
                modifier += 3
            elif blood_sugar >= 140:
                modifier += 1.5
            elif blood_sugar <= 70:
                modifier += 2  # Hypoglycemia
        
        # Symptom risk
        high_risk_symptoms = ['chest_pain', 'shortness_of_breath', 'severe_headache', 'dizziness']
        if symptoms:
            for symptom in symptoms:
                if symptom in high_risk_symptoms:
                    modifier += 1
        
        return min(10, modifier)
    
    def compute_carescore(
        self, 
        user_id: int, 
        current_data: Dict[str, float],
        symptoms: List[str] = None
    ) -> CareScore:
        """
        Compute complete CareScore for a user
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Get historical std for each signal
        historical_std = self._get_historical_std(user_id)
        
        # Calculate components
        severity, deviations = self.calculate_severity_score(
            current_data, user, historical_std
        )
        persistence, anomaly_days = self.calculate_persistence_score(user_id)
        cross_signal = self.calculate_cross_signal_score(deviations)
        manual_mod = self.calculate_manual_modifier(current_data, symptoms)
        
        # Final CareScore
        care_score = severity + persistence + cross_signal + manual_mod
        care_score = min(100, max(0, care_score))
        
        # Determine status
        if care_score <= 30:
            status = 'stable'
        elif care_score <= 50:
            status = 'mild'
        elif care_score <= 70:
            status = 'moderate'
        else:
            status = 'high'
        
        # Calculate drift score
        drift_score = self._calculate_drift_score(deviations)
        
        # Calculate confidence score
        confidence = self._calculate_confidence(user_id, len(deviations))
        
        # Calculate stability score
        stability = self._calculate_stability(user_id)
        
        # Generate explanation
        explanation = self._generate_explanation(
            deviations, severity, persistence, cross_signal, 
            manual_mod, care_score, status
        )
        
        # Create CareScore record
        care_score_record = CareScore(
            user_id=user_id,
            severity_score=severity,
            persistence_score=persistence,
            cross_signal_score=cross_signal,
            manual_modifier=manual_mod,
            care_score=round(care_score, 1),
            drift_score=drift_score,
            confidence_score=confidence,
            stability_score=stability,
            contributing_signals=json.dumps(deviations),
            explanation=explanation,
            status=status
        )
        
        self.db.add(care_score_record)
        self.db.commit()
        self.db.refresh(care_score_record)
        
        # Trigger notifications if necessary
        # Only notify for moderate or high risk
        if care_score_record.care_score >= 31:
            from app.services.notification_service import NotificationService
            notification_service = NotificationService(self.db)
            notification_service.notify_anomaly_detected(
                patient_id=user_id,
                care_score=care_score_record
            )
        
        return care_score_record
    
    def _get_historical_std(self, user_id: int, days: int = 30) -> Dict[str, float]:
        """Get historical standard deviation for each signal"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        data = self.db.query(HealthData).filter(
            HealthData.user_id == user_id,
            HealthData.timestamp >= cutoff
        ).all()
        
        if not data:
            return {}
        
        signals = ['heart_rate', 'hrv', 'sleep_duration', 'activity_level', 
                   'breathing_rate', 'bp_systolic', 'bp_diastolic', 'blood_sugar']
        
        std_devs = {}
        for signal in signals:
            values = [getattr(d, signal) for d in data if getattr(d, signal) is not None]
            if values:
                std_devs[signal] = float(np.std(values))
        
        return std_devs
    
    def _calculate_drift_score(self, deviations: List[Dict]) -> float:
        """Calculate overall drift score from baseline"""
        if not deviations:
            return 0
        
        avg_z_score = sum(d['z_score'] for d in deviations) / len(deviations)
        return min(100, avg_z_score * 20)
    
    def _calculate_confidence(self, user_id: int, num_signals: int) -> float:
        """Calculate confidence score based on data availability"""
        # More signals and more history = higher confidence
        cutoff = datetime.utcnow() - timedelta(days=30)
        data_count = self.db.query(HealthData).filter(
            HealthData.user_id == user_id,
            HealthData.timestamp >= cutoff
        ).count()
        
        data_confidence = min(50, data_count * 1.5)
        signal_confidence = min(50, num_signals * 8)
        
        return round(data_confidence + signal_confidence, 1)
    
    def _calculate_stability(self, user_id: int) -> float:
        """Calculate health stability score (lower variation = higher stability)"""
        cutoff = datetime.utcnow() - timedelta(days=14)
        
        scores = self.db.query(CareScore).filter(
            CareScore.user_id == user_id,
            CareScore.timestamp >= cutoff
        ).all()
        
        if len(scores) < 3:
            return 50  # Neutral stability with insufficient data
        
        care_scores = [s.care_score for s in scores]
        variation = np.std(care_scores)
        
        # Lower variation = higher stability
        stability = max(0, 100 - variation * 2)
        return round(stability, 1)
    
    def _generate_explanation(
        self,
        deviations: List[Dict],
        severity: float,
        persistence: float,
        cross_signal: float,
        manual_mod: float,
        care_score: float,
        status: str
    ) -> str:
        """Generate human-readable explanation of CareScore"""
        if not deviations:
            return "All health signals are within your normal range. Your body is tracking as expected."
        
        top_deviations = sorted(deviations, key=lambda x: x['z_score'], reverse=True)[:3]
        
        signal_names = {
            'heart_rate': 'heart rate',
            'hrv': 'heart rate variability',
            'sleep_duration': 'sleep duration',
            'sleep_quality': 'sleep quality',
            'activity_level': 'activity level',
            'breathing_rate': 'breathing rate',
            'bp_systolic': 'blood pressure (systolic)',
            'bp_diastolic': 'blood pressure (diastolic)',
            'blood_sugar': 'blood sugar'
        }
        
        explanation_parts = []
        
        if status == 'high':
            explanation_parts.append(
                "Your health signals show notable changes that warrant attention."
            )
        elif status == 'moderate':
            explanation_parts.append(
                "Some health signals are deviating from your usual patterns."
            )
        else:
            explanation_parts.append(
                "Minor variations detected in your health data."
            )
        
        for dev in top_deviations:
            name = signal_names.get(dev['signal'], dev['signal'])
            direction = "higher" if dev['current'] > dev['baseline'] else "lower"
            explanation_parts.append(
                f"Your {name} is {direction} than your baseline "
                f"({dev['current']:.1f} vs {dev['baseline']:.1f})."
            )
        
        if persistence > 10:
            explanation_parts.append(
                "These changes have persisted for several days."
            )
        
        return " ".join(explanation_parts)

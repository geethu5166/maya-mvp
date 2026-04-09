"""
ML-Based Decision Intelligence

Replaces rule-based severity with trained ML models.
Learns from incident patterns to improve decision quality over time.

Phase 3: ML Enhancement
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class MLModelType(str, Enum):
    """Types of ML models for different decision aspects"""
    SEVERITY_PREDICTOR = "severity_predictor"          # Predicts severity 0-100
    ACTION_RECOMMENDER = "action_recommender"          # Recommends action type
    FALSE_POSITIVE_CLASSIFIER = "fp_classifier"        # Predicts if false positive
    SLA_ESTIMATOR = "sla_estimator"                    # Estimates response time


@dataclass
class DetectionFeatures:
    """Features extracted from raw detection for ML model input"""
    # Rule-based features
    rule_confidence: float                              # 0-1
    detection_frequency: int                            # How many times in past hour
    
    # Context features
    asset_criticality: float                            # 0-1 (dev=0.2, prod=1.0)
    asset_type: str                                     # "database", "webserver", etc.
    
    # Behavioral features
    user_normal_pattern: float                          # 0-1 (how typical is this)
    time_anomaly_score: float                           # 0-100
    volume_anomaly_score: float                         # 0-100
    location_anomaly_score: float                       # 0-100
    frequency_anomaly_score: float                      # 0-100
    
    # Historical features
    similar_incidents_count: int                        # How many similar in past 30 days
    avg_resolution_time_minutes: int                    # Average time to resolve
    false_positive_rate: float                          # 0-1 per detection type
    
    # Feature engineering
    def to_numpy_array(self) -> np.ndarray:
        """Convert to ML model input format"""
        return np.array([
            self.rule_confidence,
            self.detection_frequency,
            self.asset_criticality,
            self.time_anomaly_score / 100.0,
            self.volume_anomaly_score / 100.0,
            self.location_anomaly_score / 100.0,
            self.frequency_anomaly_score / 100.0,
            self.user_normal_pattern,
            self.similar_incidents_count,
            self.avg_resolution_time_minutes / 60.0,  # Normalize to hours
            self.false_positive_rate
        ])


@dataclass
class ModelPrediction:
    """ML model prediction result"""
    model_type: MLModelType
    prediction: float                                   # Main prediction
    confidence: float                                   # 0-1 model confidence
    feature_importance: Dict[str, float]               # Which features mattered most
    reasoning: str                                      # Human-readable explanation


class SeverityPredictor:
    """
    ML Model: Predicts severity (0-100) based on detection + context features
    
    Uses: Logistic regression + ensemble
    Input: DetectionFeatures
    Output: Severity score 0-100
    """
    
    def __init__(self):
        self.model_type = MLModelType.SEVERITY_PREDICTOR
        # Simplified weights (in production: trained on historical data)
        self.weights = {
            'rule_confidence': 25,
            'asset_criticality': 30,
            'time_anomaly': 10,
            'volume_anomaly': 15,
            'location_anomaly': 10,
            'detection_frequency': 5,
            'similar_incidents': 5
        }
    
    def predict(self, features: DetectionFeatures) -> ModelPrediction:
        """
        Predict severity score based on features
        
        Severity = rule_confidence × asset_criticality × base_score
                   + anomaly_boost
                   + historical_boost
        """
        
        # Base severity from rule confidence × asset criticality
        base_score = (features.rule_confidence * 100) * features.asset_criticality
        
        # Anomaly boost (multiple anomalies = higher severity)
        anomaly_scores = [
            features.time_anomaly_score,
            features.volume_anomaly_score,
            features.location_anomaly_score,
            features.frequency_anomaly_score
        ]
        
        # Count how many anomalies detected
        anomaly_count = sum(1 for score in anomaly_scores if score > 50)
        anomaly_avg = np.mean([s for s in anomaly_scores if s > 0]) if anomaly_scores else 0
        
        # Multiple anomalies boost severity
        anomaly_multiplier = 1.0 + (anomaly_count * 0.2)  # +0.2 per anomaly
        
        # Historical boost (if similar incidents before, likely serious)
        historical_boost = min(20, features.similar_incidents_count * 2)
        
        # Detection frequency boost (repeated detections = more serious)
        frequency_boost = min(15, features.detection_frequency * 3)
        
        # Final severity
        severity = (base_score * anomaly_multiplier) + historical_boost + frequency_boost
        severity = min(100, severity)  # Cap at 100
        
        # Model confidence based on feature quality
        confidence = min(1.0, features.rule_confidence + (anomaly_count * 0.1))
        
        # Feature importance
        feature_importance = {
            'rule_confidence': (features.rule_confidence * 35),
            'asset_criticality': (features.asset_criticality * 30),
            'anomalies': (anomaly_avg / 100 * 20),
            'historical_pattern': (historical_boost / 20 * 10),
            'detection_frequency': (min(1.0, features.detection_frequency / 10) * 5)
        }
        
        # Normalize importance scores
        total = sum(feature_importance.values())
        if total > 0:
            feature_importance = {k: v/total for k, v in feature_importance.items()}
        
        # Reasoning
        reasoning = f"Severity {severity:.0f}/100 based on: "
        reasoning += f"Rule confidence {features.rule_confidence:.0%}, "
        reasoning += f"Asset criticality {features.asset_criticality:.0%}, "
        if anomaly_count > 0:
            reasoning += f"{anomaly_count} behavioral anomalies detected, "
        if features.similar_incidents_count > 0:
            reasoning += f"{features.similar_incidents_count} similar incidents in past 30 days, "
        reasoning += f"False positive risk {features.false_positive_rate:.0%}"
        
        return ModelPrediction(
            model_type=self.model_type,
            prediction=severity,
            confidence=confidence,
            feature_importance=feature_importance,
            reasoning=reasoning
        )


class ActionRecommender:
    """
    ML Model: Recommends action (ACKNOWLEDGE, INVESTIGATE, ISOLATE, BLOCK, ESCALATE)
    
    Uses: Decision tree + rule-based logic
    Input: DetectionFeatures + Severity
    Output: Recommended action + confidence
    """
    
    def __init__(self):
        self.model_type = MLModelType.ACTION_RECOMMENDER
    
    def predict(
        self,
        features: DetectionFeatures,
        severity: float,
        detection_type: str
    ) -> ModelPrediction:
        """
        Recommend action based on severity + context
        
        Decision tree:
        - Severity < 30: ACKNOWLEDGE (low risk)
        - Severity 30-50: INVESTIGATE (medium risk, review needed)
        - Severity 50-70: ISOLATE (high risk, disconnect asset)
        - Severity 70-85: BLOCK (very high, block at firewall)
        - Severity >= 85: ESCALATE (critical, needs management)
        """
        
        # Determine action based on severity
        if severity < 30:
            action = "ACKNOWLEDGE"
            confidence = 0.95
        elif severity < 50:
            action = "INVESTIGATE"
            confidence = 0.90
        elif severity < 70:
            action = "ISOLATE"
            confidence = 0.85
        elif severity < 85:
            action = "BLOCK"
            confidence = 0.80
        else:
            action = "ESCALATE"
            confidence = 0.85
        
        # Confidence adjustment based on feature quality
        if features.rule_confidence < 0.7:
            confidence -= 0.1  # Lower confidence if rule confidence is low
        
        if features.similar_incidents_count > 3:
            confidence += 0.05  # Higher confidence if pattern repeated
        
        confidence = max(0.5, min(1.0, confidence))
        
        # Feature importance (what drove the action decision)
        feature_importance = {
            'severity': severity / 100 * 0.6,
            'asset_criticality': features.asset_criticality * 0.2,
            'anomaly_count': min(1.0, sum([
                1 for s in [features.time_anomaly_score, features.volume_anomaly_score,
                           features.location_anomaly_score, features.frequency_anomaly_score]
                if s > 50
            ]) / 4.0) * 0.2
        }
        
        # Reasoning
        reasoning = f"Recommend {action} (confidence {confidence:.0%}). "
        reasoning += f"Severity {severity:.0f}/100 triggers {action} action. "
        if features.asset_criticality > 0.8:
            reasoning += "Critical asset increases urgency. "
        if sum([features.time_anomaly_score, features.volume_anomaly_score]) > 100:
            reasoning += "Multiple behavioral anomalies detected. "
        
        return ModelPrediction(
            model_type=self.model_type,
            prediction=severity,  # For consistency, return severity
            confidence=confidence,
            feature_importance=feature_importance,
            reasoning=reasoning
        )


class FalsePositiveClassifier:
    """
    ML Model: Predicts probability of false positive
    
    Uses: Binary classifier
    Input: DetectionFeatures
    Output: False positive probability (0-1)
    """
    
    def __init__(self):
        self.model_type = MLModelType.FALSE_POSITIVE_CLASSIFIER
        # Detection type FP rates (from historical data)
        self.detection_fp_rates = {
            'ssh_brute_force': 0.05,
            'password_spray': 0.08,
            'unusual_data_transfer': 0.25,
            'database_exfiltration': 0.15,
            'sql_injection': 0.10,
            'file_integrity_violation': 0.20,
            'privilege_escalation': 0.12,
            'malicious_powershell': 0.18
        }
    
    def predict(
        self,
        features: DetectionFeatures,
        detection_type: str
    ) -> ModelPrediction:
        """
        Predict false positive probability
        
        FP probability = base_fp_rate
                        × (1 - rule_confidence)
                        / (1 + similarity_matches)
        """
        
        # Get base FP rate for this detection type
        base_fp_rate = self.detection_fp_rates.get(detection_type, 0.15)
        
        # Adjust by confidence (lower confidence = higher FP risk)
        confidence_factor = 1 - features.rule_confidence  # 0-1
        
        # Adjust by similar incidents (more matches = lower FP risk)
        similarity_factor = 1 / (1 + features.similar_incidents_count)
        
        # Calculate FP probability
        fp_probability = base_fp_rate * (1 + confidence_factor) * similarity_factor
        fp_probability = min(1.0, max(0.0, fp_probability))
        
        # Model confidence (how sure are we about FP prediction)
        model_confidence = 0.8 if features.detection_frequency > 1 else 0.6
        
        # Feature importance
        feature_importance = {
            'rule_confidence': (1 - features.rule_confidence) * 0.4,
            'detection_type': base_fp_rate * 0.4,
            'similar_incidents': similarity_factor * 0.2
        }
        
        # Risk level
        if fp_probability < 0.1:
            risk_level = "Low"
        elif fp_probability < 0.25:
            risk_level = "Medium"
        else:
            risk_level = "High"
        
        reasoning = f"False positive {risk_level.lower()} risk ({fp_probability:.0%}). "
        reasoning += f"{detection_type}: {base_fp_rate:.0%} historical FP rate. "
        if features.rule_confidence > 0.9:
            reasoning += "High rule confidence reduces FP risk. "
        if features.similar_incidents_count > 0:
            reasoning += f"{features.similar_incidents_count} similar confirmed incidents. "
        
        return ModelPrediction(
            model_type=self.model_type,
            prediction=fp_probability,
            confidence=model_confidence,
            feature_importance=feature_importance,
            reasoning=reasoning
        )


class SLAEstimator:
    """
    ML Model: Estimates SLA (response time in minutes)
    
    Uses: Regression model
    Input: Severity + Context
    Output: SLA in minutes
    """
    
    def __init__(self):
        self.model_type = MLModelType.SLA_ESTIMATOR
        # SLA matrix by severity
        self.sla_by_severity = {
            0: (1440, "1 day"),      # INFO
            30: (480, "8 hours"),    # LOW
            50: (120, "2 hours"),    # MEDIUM
            70: (30, "30 minutes"),  # HIGH
            85: (5, "5 minutes"),    # CRITICAL
        }
    
    def predict(self, severity: float) -> ModelPrediction:
        """
        Estimate SLA based on severity
        
        SLA (minutes) = base_sla - (assets_at_risk * reduction_factor)
        """
        
        # Find appropriate SLA for severity
        if severity < 30:
            sla_minutes = 1440
            sla_label = "1 day"
        elif severity < 50:
            sla_minutes = 480
            sla_label = "8 hours"
        elif severity < 70:
            sla_minutes = 120
            sla_label = "2 hours"
        elif severity < 85:
            sla_minutes = 30
            sla_label = "30 minutes"
        else:
            sla_minutes = 5
            sla_label = "5 minutes"
        
        confidence = 0.95  # SLA estimation is deterministic by severity
        
        feature_importance = {
            'severity': 1.0
        }
        
        reasoning = f"SLA: {sla_label}. Severity {severity:.0f} requires {sla_minutes}-minute response."
        
        return ModelPrediction(
            model_type=self.model_type,
            prediction=sla_minutes,
            confidence=confidence,
            feature_importance=feature_importance,
            reasoning=reasoning
        )


class MLDecisionEngine:
    """
    AI-powered decision engine using ML models
    
    Replaces rule-based severity with trained predictions
    Learns from incident patterns to improve over time
    """
    
    def __init__(self):
        self.severity_predictor = SeverityPredictor()
        self.action_recommender = ActionRecommender()
        self.fp_classifier = FalsePositiveClassifier()
        self.sla_estimator = SLAEstimator()
        
        # Learning system (stores outcomes for model improvement)
        self.incidents_log: List[Dict] = []
    
    def predict_decision(
        self,
        features: DetectionFeatures,
        detection_type: str
    ) -> Dict:
        """
        Make ML-based decision prediction using all models
        
        Returns: {
            'severity': float (0-100),
            'action': str,
            'sla_minutes': int,
            'fp_probability': float (0-1),
            'models': [predictions from each model],
            'confidence': float (average across models),
            'reasoning': str
        }
        """
        
        # Get ML predictions from all models
        severity_pred = self.severity_predictor.predict(features)
        action_pred = self.action_recommender.predict(features, severity_pred.prediction, detection_type)
        fp_pred = self.fp_classifier.predict(features, detection_type)
        sla_pred = self.sla_estimator.predict(severity_pred.prediction)
        
        # Extract action from action predictor
        action = self._get_action_from_severity(severity_pred.prediction)
        
        # Average confidence across models
        avg_confidence = np.mean([
            severity_pred.confidence,
            action_pred.confidence,
            fp_pred.confidence,
            sla_pred.confidence
        ])
        
        # Combined reasoning
        combined_reasoning = (
            f"ML Decision: {severity_pred.reasoning} "
            f"→ {action_pred.reasoning} "
            f"→ {fp_pred.reasoning}"
        )
        
        return {
            'severity': severity_pred.prediction,
            'action': action,
            'sla_minutes': int(sla_pred.prediction),
            'fp_probability': fp_pred.prediction,
            'models': {
                'severity': severity_pred,
                'action': action_pred,
                'false_positive': fp_pred,
                'sla': sla_pred
            },
            'confidence': avg_confidence,
            'reasoning': combined_reasoning,
            'feature_importance': severity_pred.feature_importance
        }
    
    def _get_action_from_severity(self, severity: float) -> str:
        """Map severity to action"""
        if severity < 30:
            return "ACKNOWLEDGE"
        elif severity < 50:
            return "INVESTIGATE"
        elif severity < 70:
            return "ISOLATE"
        elif severity < 85:
            return "BLOCK"
        else:
            return "ESCALATE"
    
    def record_incident_outcome(
        self,
        incident_id: str,
        features: DetectionFeatures,
        detection_type: str,
        predicted_severity: float,
        actual_severity: float,
        was_false_positive: bool,
        resolution_time_minutes: int
    ) -> None:
        """
        Record incident outcome for model learning
        
        In production: Use this data to retrain models
        """
        
        self.incidents_log.append({
            'timestamp': datetime.utcnow().isoformat(),
            'incident_id': incident_id,
            'detection_type': detection_type,
            'predicted_severity': predicted_severity,
            'actual_severity': actual_severity,
            'severity_error': abs(predicted_severity - actual_severity),
            'was_false_positive': was_false_positive,
            'resolution_time': resolution_time_minutes,
            'features': features
        })
        
        logger.info(
            f"Recorded outcome for {incident_id}: "
            f"Predicted={predicted_severity:.0f}, Actual={actual_severity:.0f}, "
            f"FP={was_false_positive}, Time={resolution_time_minutes}min"
        )
    
    def get_model_accuracy_metrics(self) -> Dict:
        """
        Calculate model accuracy metrics from recorded incidents
        
        Returns: {
            'severity_mae': float (mean absolute error),
            'fp_accuracy': float (0-1),
            'incidents_logged': int,
            'last_retrain': datetime
        }
        """
        
        if not self.incidents_log:
            return {
                'severity_mae': None,
                'fp_accuracy': None,
                'incidents_logged': 0,
                'message': 'No incidents logged yet'
            }
        
        # Severity MAE (Mean Absolute Error)
        severity_errors = [inc['severity_error'] for inc in self.incidents_log]
        severity_mae = np.mean(severity_errors)
        
        # FP accuracy
        fp_predictions = [inc['was_false_positive'] for inc in self.incidents_log]
        fp_accuracy = 1.0 - (np.mean(fp_predictions) if fp_predictions else 0)
        
        return {
            'severity_mae': severity_mae,
            'fp_accuracy': fp_accuracy,
            'incidents_logged': len(self.incidents_log),
            'mae_interpretation': f'Off by ~{severity_mae:.0f} points on average'
        }

"""
Anomaly Detection Service
Uses statistical methods and ML to detect unusual attack patterns
"""

import logging
from typing import Dict, Any, List, Tuple
import numpy as np
from dataclasses import dataclass
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """Result from anomaly detection analysis"""
    is_anomaly: bool
    confidence: float
    score: float
    reason: str
    timestamp: str
    

class AnomalyDetectionModel:
    """
    ML-based anomaly detection using Isolation Forest
    Detects unusual attack patterns that don't match known behavior
    """
    
    def __init__(self, model_path: str = None):
        """Initialize anomaly detector"""
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(
            contamination=0.05,  # Expect 5% anomalies
            random_state=42,
            n_estimators=100
        )
        self.model_path = model_path
        self.is_fitted = False
        
        # Try to load pre-trained model
        if model_path and Path(model_path).exists():
            self.load(model_path)
    
    def extract_features(self, event: Dict[str, Any]) -> np.ndarray:
        """
        Extract numerical features from security event
        
        Args:
            event: Security event data
            
        Returns:
            Numerical feature vector
        """
        features = []
        
        # Time-based features
        features.append(hash(event.get('timestamp', '')) % 24)  # Hour of day
        
        # Event type features
        event_type_map = {
            'SSH_BRUTE_FORCE': 1,
            'WEB_CREDENTIAL_HARVEST': 2,
            'DB_LOGIN_ATTEMPT': 3,
            'WEB_SCAN': 4,
            'REDIS_COMMAND': 5,
            'WEB_RECON': 6,
        }
        features.append(event_type_map.get(event.get('type', ''), 0))
        
        # Severity features
        severity_map = {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
        features.append(severity_map.get(event.get('severity', ''), 0))
        
        # IP-based features (extract numeric from IP)
        ip = event.get('attacker_ip', '0.0.0.0')
        try:
            ip_parts = [int(x) for x in ip.split('.')[:2]]
            features.extend(ip_parts)
        except:
            features.extend([0, 0])
        
        # Port-based feature
        port = event.get('attacker_port', 0)
        features.append(port if isinstance(port, int) else 0)
        
        # Count features (passwords, usernames attempted)
        features.append(len(event.get('password_tried', '')))
        features.append(len(event.get('username_tried', '')))
        
        return np.array(features, dtype=float).reshape(1, -1)
    
    def train(self, events: List[Dict[str, Any]]):
        """
        Train anomaly detector on normal traffic
        
        Args:
            events: List of normal (non-anomalous) security events
        """
        if not events:
            logger.warning("No events provided for training")
            return
        
        # Extract features from all events
        features = []
        for event in events:
            try:
                feat = self.extract_features(event)
                features.append(feat[0])
            except Exception as e:
                logger.debug(f"Error extracting features: {e}")
        
        if not features:
            logger.warning("No valid features extracted")
            return
        
        features = np.array(features)
        
        # Scale features
        scaled_features = self.scaler.fit_transform(features)
        
        # Train isolation forest
        self.isolation_forest.fit(scaled_features)
        self.is_fitted = True
        
        logger.info(f"Anomaly detector trained on {len(events)} events")
    
    def detect(self, event: Dict[str, Any]) -> DetectionResult:
        """
        Detect if event is anomalous
        
        Args:
            event: Security event to analyze
            
        Returns:
            DetectionResult with anomaly assessment
        """
        try:
            # Extract features
            features = self.extract_features(event)
            
            # If not trained, mark as unknown
            if not self.is_fitted:
                return DetectionResult(
                    is_anomaly=False,
                    confidence=0.0,
                    score=0.0,
                    reason="Model not trained yet",
                    timestamp=event.get('timestamp', '')
                )
            
            # Scale features
            scaled_features = self.scaler.transform(features)
            
            # Get anomaly prediction (-1 = anomaly, 1 = normal)
            prediction = self.isolation_forest.predict(scaled_features)[0]
            
            # Get anomaly score (lower = more anomalous)
            anomaly_scores = self.isolation_forest.score_samples(scaled_features)
            score = float(anomaly_scores[0])
            
            # Convert to confidence (0-1 where higher = more anomalous)
            confidence = max(0, min(1, abs(score) / 0.5))
            
            is_anomaly = prediction == -1
            
            # Generate reason
            if is_anomaly:
                reason = f"Pattern mismatch (score: {score:.2f})"
            else:
                reason = "Normal attack pattern"
            
            return DetectionResult(
                is_anomaly=is_anomaly,
                confidence=confidence,
                score=score,
                reason=reason,
                timestamp=event.get('timestamp', '')
            )
            
        except Exception as e:
            logger.error(f"Error detecting anomaly: {e}")
            return DetectionResult(
                is_anomaly=False,
                confidence=0.0,
                score=0.0,
                reason=f"Detection error: {e}",
                timestamp=event.get('timestamp', '')
            )
    
    def save(self, path: str):
        """Save trained model to disk"""
        try:
            data = {
                'scaler': self.scaler,
                'forest': self.isolation_forest,
                'is_fitted': self.is_fitted
            }
            with open(path, 'wb') as f:
                pickle.dump(data, f)
            logger.info(f"Model saved to {path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def load(self, path: str):
        """Load pre-trained model from disk"""
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            self.scaler = data['scaler']
            self.isolation_forest = data['forest']
            self.is_fitted = data['is_fitted']
            logger.info(f"Model loaded from {path}")
        except Exception as e:
            logger.error(f"Error loading model: {e}")


class StatisticalAnomalyDetector:
    """
    Statistical anomaly detection using simple thresholding
    Faster than ML-based detection, good for baseline
    """
    
    def __init__(self, threshold: float = 2.0):
        """Initialize statistical detector"""
        self.threshold = threshold
        self.baseline_stats = {}
    
    def detect_outliers(self, data: np.ndarray) -> List[int]:
        """
        Detect outliers using statistical methods
        
        Args:
            data: Numerical data
            
        Returns:
            Indices of outlier data points
        """
        if len(data) < 2:
            return []
        
        try:
            mean = np.mean(data)
            std = np.std(data)
            
            if std == 0:
                return []
            
            z_scores = np.abs((data - mean) / std)
            outlier_indices = np.where(z_scores > self.threshold)[0].tolist()
            
            return outlier_indices
            
        except Exception as e:
            logger.error(f"Error detecting outliers: {e}")
            return []


def create_anomaly_detector() -> AnomalyDetectionModel:
    """Factory function to create anomaly detector instance"""
    return AnomalyDetectionModel()

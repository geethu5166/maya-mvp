"""
Advanced ML-Powered Threat Detection Engine.
Implements multiple machine learning models for autonomous threat detection.

Models:
1. Anomaly Detection (Isolation Forest) - Detects unusual behavior
2. Threat Classification (XGBoost) - Categorizes event types
3. Risk Scoring (Ensemble) - Calculates threat severity
4. Behavioral Analysis (Statistical) - Identifies patterns
5. Entity Deduplication (Fuzzy Matching) - Reduces noise
"""

import logging
import pickle
import asyncio
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
import xgboost as xgb
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class MLPrediction:
    """Machine learning prediction result"""
    is_anomaly: bool
    anomaly_score: float  # 0-1, higher = more anomalous
    threat_type: str  # SSH_BRUTE_FORCE, WEB_SCAN, etc.
    threat_confidence: float  # 0-1
    risk_score: int  # 0-100
    risk_level: str  # CRITICAL, HIGH, MEDIUM, LOW
    behavioral_cluster: int  # Group ID (-1 = singleton)
    is_duplicate: bool
    duplicate_similarity: float  # 0-1
    recommendation: str  # Suggested response


class AnomalyDetectionModel:
    """Isolation Forest-based anomaly detection"""
    
    def __init__(self, contamination: float = 0.1):
        """
        Initialize anomaly detector.
        
        Args:
            contamination: Expected fraction of anomalies (0-1)
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_depth=10
        )
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = []
    
    async def train(self, events: List[Dict[str, Any]]) -> bool:
        """
        Train anomaly detection model on historical events.
        
        Args:
            events: List of events with numerical features
            
        Returns:
            Success status
        """
        try:
            # Feature extraction
            features = self._extract_features(events)
            if features.empty:
                logger.warning("No features to train on")
                return False
            
            # Scale features
            X = self.scaler.fit_transform(features)
            
            # Train model
            self.model.fit(X)
            self.feature_names = features.columns.tolist()
            self.is_trained = True
            
            logger.info(f"✓ Anomaly detection model trained on {len(events)} events")
            return True
        except Exception as e:
            logger.error(f"✗ Training failed: {e}")
            return False
    
    async def score(self, event: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Score an event for anomalies.
        
        Args:
            event: Single event to analyze
            
        Returns:
            (is_anomaly, anomaly_score)
        """
        if not self.is_trained:
            return False, 0.5
        
        try:
            features = self._extract_features([event])
            X = self.scaler.transform(features)
            
            # Get anomaly score (-1 to 1, higher = more anomalous)
            anomaly_label = self.model.predict(X)[0]
            anomaly_score = self.model.score_samples(X)[0]
            
            # Normalize to 0-1
            normalized_score = 1 / (1 + np.exp(-anomaly_score))
            
            return (anomaly_label == -1), float(normalized_score)
        except Exception as e:
            logger.warning(f"Scoring failed: {e}")
            return False, 0.5
    
    def _extract_features(self, events: List[Dict[str, Any]]) -> pd.DataFrame:
        """Extract numerical features from events"""
        features_list = []
        
        for event in events:
            feature_dict = {
                'source_ip_parts': sum(1 for x in str(event.get('source_ip', '')).split('.') if x.isdigit()),
                'dest_ip_parts': sum(1 for x in str(event.get('destination_ip', '')).split('.') if x.isdigit()),
                'description_length': len(str(event.get('description', ''))),
                'metadata_size': len(json.dumps(event.get('metadata', {}))),
                'severity_score': {'CRITICAL': 4, 'HIGH': 3, 'MEDIUM': 2, 'LOW': 1, 'INFO': 0}.get(
                    event.get('severity', 'INFO'), 0),
                'has_user_agent': 1 if event.get('user_agent') else 0,
                'has_command': 1 if event.get('command') else 0,
            }
            features_list.append(feature_dict)
        
        return pd.DataFrame(features_list) if features_list else pd.DataFrame()


class ThreatClassifier:
    """XGBoost-based threat type classifier"""
    
    def __init__(self, num_classes: int = 6):
        """
        Initialize threat classifier.
        
        Args:
            num_classes: Number of threat types
        """
        self.num_classes = num_classes
        self.model = xgb.XGBClassifier(
            objective='multi:softprob',
            num_class=num_classes,
            random_state=42,
            n_estimators=100,
            max_depth=8,
            learning_rate=0.1,
            eval_metric='mlogloss'
        )
        self.scaler = StandardScaler()
        self.label_encoder = {
            'SSH_BRUTE_FORCE': 0,
            'WEB_SCAN': 1,
            'DB_PROBE': 2,
            'ANOMALY': 3,
            'HONEYPOT_INTERACTION': 4,
            'CANARY_TRIGGER': 5
        }
        self.is_trained = False
    
    async def train(self, events: List[Dict[str, Any]], labels: List[str]) -> bool:
        """
        Train threat classifier.
        
        Args:
            events: Training events
            labels: Threat type labels
            
        Returns:
            Success status
        """
        try:
            features = self._extract_features(events)
            if features.empty:
                return False
            
            X = self.scaler.fit_transform(features)
            y = np.array([self.label_encoder.get(l, 0) for l in labels])
            
            self.model.fit(X, y)
            self.is_trained = True
            
            logger.info(f"✓ Threat classifier trained on {len(events)} events")
            return True
        except Exception as e:
            logger.error(f"✗ Training failed: {e}")
            return False
    
    async def predict(self, event: Dict[str, Any]) -> Tuple[str, float]:
        """
        Predict threat type and confidence.
        
        Args:
            event: Event to classify
            
        Returns:
            (threat_type, confidence)
        """
        if not self.is_trained:
            return 'UNKNOWN', 0.5
        
        try:
            features = self._extract_features([event])
            X = self.scaler.transform(features)
            
            probs = self.model.predict_proba(X)[0]
            pred_class = np.argmax(probs)
            confidence = float(probs[pred_class])
            
            # Reverse label encoder
            threat_type = [k for k, v in self.label_encoder.items() if v == pred_class][0]
            
            return threat_type, confidence
        except Exception as e:
            logger.warning(f"Prediction failed: {e}")
            return 'UNKNOWN', 0.5
    
    def _extract_features(self, events: List[Dict[str, Any]]) -> pd.DataFrame:
        """Extract features for classification"""
        features_list = []
        
        for event in events:
            feature_dict = {
                'port_number': int(str(event.get('destination_port', '0')).split('/')[-1]) if event.get('destination_port') else 0,
                'is_internal': 1 if str(event.get('destination_ip', '').startswith(('192.168', '10.', '172.'))) else 0,
                'description_word_count': len(str(event.get('description', '')).split()),
                'has_credentials': 1 if any(x in str(event).lower() for x in ['password', 'user', 'login']) else 0,
                'has_exploit': 1 if any(x in str(event).lower() for x in ['exploit', 'shellcode', 'payload']) else 0,
                'has_scan': 1 if any(x in str(event).lower() for x in ['scan', 'nmap', 'port']) else 0,
            }
            features_list.append(feature_dict)
        
        return pd.DataFrame(features_list) if features_list else pd.DataFrame()


class RiskScoringEngine:
    """Ensemble-based risk scoring system"""
    
    def __init__(self):
        """Initialize risk scoring engine"""
        self.severity_weights = {
            'CRITICAL': 1.0,
            'HIGH': 0.75,
            'MEDIUM': 0.5,
            'LOW': 0.25,
            'INFO': 0.1
        }
        self.threat_type_weights = {
            'SSH_BRUTE_FORCE': 0.8,
            'WEB_SCAN': 0.7,
            'DB_PROBE': 0.85,
            'ANOMALY': 0.6,
            'HONEYPOT_INTERACTION': 0.95,
            'CANARY_TRIGGER': 0.9,
            'UNKNOWN': 0.5
        }
    
    async def calculate_risk(self, 
                            anomaly_score: float,
                            threat_confidence: float,
                            severity: str,
                            threat_type: str,
                            threat_intel_match: bool = False) -> Tuple[int, str]:
        """
        Calculate overall risk score using ensemble method.
        
        Args:
            anomaly_score: Anomaly detection score (0-1)
            threat_confidence: Classifier confidence (0-1)
            severity: Event severity level
            threat_type: Classified threat type
            threat_intel_match: Whether threat matched intelligence database
            
        Returns:
            (risk_score: 0-100, risk_level: CRITICAL/HIGH/MEDIUM/LOW)
        """
        # Component scores
        severity_score = self.severity_weights.get(severity, 0.5) * 100
        threat_type_score = self.threat_type_weights.get(threat_type, 0.5) * 100
        anomaly_score_normalized = anomaly_score * 100
        intel_score = 100 if threat_intel_match else 0
        
        # Ensemble scoring (weighted average)
        weights = {
            'severity': 0.25,
            'threat_type': 0.30,
            'anomaly': 0.25,
            'intel': 0.20
        }
        
        risk_score = int(
            severity_score * weights['severity'] +
            threat_type_score * weights['threat_type'] +
            anomaly_score_normalized * weights['anomaly'] +
            intel_score * weights['intel']
        )
        
        # Boost with threat confidence
        risk_score = min(100, int(risk_score * (0.5 + threat_confidence)))
        
        # Determine risk level
        if risk_score >= 80:
            risk_level = 'CRITICAL'
        elif risk_score >= 60:
            risk_level = 'HIGH'
        elif risk_score >= 40:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return risk_score, risk_level


class EntityDeduplicator:
    """Fuzzy matching-based entity deduplication"""
    
    def __init__(self, threshold: float = 0.85):
        """
        Initialize deduplicator.
        
        Args:
            threshold: Similarity threshold (0-1)
        """
        self.threshold = threshold
        self.known_entities = []
    
    async def add_entity(self, entity: str) -> None:
        """Add entity to known set"""
        if entity not in self.known_entities:
            self.known_entities.append(entity)
    
    async def find_duplicate(self, entity: str) -> Tuple[bool, str, float]:
        """
        Find if entity is duplicate of known entity.
        
        Args:
            entity: Entity to check
            
        Returns:
            (is_duplicate, matched_entity, similarity)
        """
        best_match = None
        best_ratio = 0
        
        for known_entity in self.known_entities:
            ratio = SequenceMatcher(None, entity.lower(), known_entity.lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = known_entity
        
        is_duplicate = best_ratio >= self.threshold
        return is_duplicate, best_match or entity, float(best_ratio)
    
    async def deduplicate(self, entities: List[str]) -> List[Tuple[str, int]]:
        """
        Group entities and return deduplicated list.
        
        Args:
            entities: List of entities to deduplicate
            
        Returns:
            List of (canonical_entity, count) tuples
        """
        groups = {}
        
        for entity in entities:
            is_dup, matched, ratio = await self.find_duplicate(entity)
            if is_dup:
                canonical = matched
            else:
                canonical = entity
                await self.add_entity(entity)
            
            if canonical not in groups:
                groups[canonical] = 0
            groups[canonical] += 1
        
        return list(groups.items())


class MLEngineService:
    """Complete ML threat detection engine"""
    
    def __init__(self):
        """Initialize complete ML engine"""
        self.anomaly_detector = AnomalyDetectionModel(contamination=0.05)
        self.threat_classifier = ThreatClassifier(num_classes=6)
        self.risk_scorer = RiskScoringEngine()
        self.entity_deduplicator = EntityDeduplicator(threshold=0.85)
        self.last_training = None
        self.training_interval = timedelta(hours=1)
    
    async def predict_threat(self, event: Dict[str, Any]) -> MLPrediction:
        """
        Complete threat prediction pipeline.
        
        Args:
            event: Event to analyze
            
        Returns:
            MLPrediction with all scores
        """
        try:
            # Step 1: Anomaly detection
            is_anomaly, anomaly_score = await self.anomaly_detector.score(event)
            
            # Step 2: Threat classification
            threat_type, threat_confidence = await self.threat_classifier.predict(event)
            
            # Step 3: Risk scoring
            severity = event.get('severity', 'INFO')
            risk_score, risk_level = await self.risk_scorer.calculate_risk(
                anomaly_score, threat_confidence, severity, threat_type
            )
            
            # Step 4: Entity deduplication
            source_ip = event.get('source_ip', '')
            is_duplicate, matched_ip, similarity = await self.entity_deduplicator.find_duplicate(source_ip)
            
            # Step 5: Generate recommendation
            recommendation = self._generate_recommendation(risk_level, threat_type, is_anomaly)
            
            return MLPrediction(
                is_anomaly=is_anomaly,
                anomaly_score=anomaly_score,
                threat_type=threat_type,
                threat_confidence=threat_confidence,
                risk_score=risk_score,
                risk_level=risk_level,
                behavioral_cluster=-1,  # TODO: Implement clustering
                is_duplicate=is_duplicate,
                duplicate_similarity=similarity,
                recommendation=recommendation
            )
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return MLPrediction(
                is_anomaly=False,
                anomaly_score=0.5,
                threat_type='UNKNOWN',
                threat_confidence=0.0,
                risk_score=50,
                risk_level='MEDIUM',
                behavioral_cluster=-1,
                is_duplicate=False,
                duplicate_similarity=0.0,
                recommendation='INVESTIGATE'
            )
    
    async def train_models(self, events: List[Dict[str, Any]]) -> bool:
        """
        Train all models on historical events.
        
        Args:
            events: Historical events for training
            
        Returns:
            Success status
        """
        try:
            if len(events) < 100:
                logger.warning(f"Need at least 100 events to train, got {len(events)}")
                return False
            
            # Train anomaly detector
            await self.anomaly_detector.train(events)
            
            # For threat classifier, we need labels (use event_type as proxy)
            labels = [e.get('event_type', 'UNKNOWN') for e in events]
            await self.threat_classifier.train(events, labels)
            
            self.last_training = datetime.now()
            logger.info("✓ All ML models trained successfully")
            return True
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return False
    
    def _generate_recommendation(self, risk_level: str, threat_type: str, is_anomaly: bool) -> str:
        """Generate recommended response"""
        if risk_level == 'CRITICAL':
            return 'BLOCK_AND_ALERT_SOC'
        elif risk_level == 'HIGH':
            return 'ISOLATE_AND_INVESTIGATE'
        elif risk_level == 'MEDIUM':
            if is_anomaly:
                return 'MONITOR_AND_LOG'
            else:
                return 'LOG_AND_TRACK'
        else:
            return 'LOG'
    
    async def should_retrain(self) -> bool:
        """Check if models should be retrained"""
        if self.last_training is None:
            return True
        return datetime.now() - self.last_training >= self.training_interval


# Global ML engine instance
ml_engine = MLEngineService()

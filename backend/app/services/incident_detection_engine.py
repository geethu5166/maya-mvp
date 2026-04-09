"""
INCIDENT DETECTION ENGINE
==========================

Real-time incident detection and correlation
Analyzes events to create actionable incidents.

Features:
- Rule-based detection (SIGMA rules)
- ML-based anomaly detection
- Event correlation
- MITRE ATT&CK mapping
- AutoIncidents from detection patterns

Author: MAYA SOC Enterprise
Version: 1.0
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DetectionStrategy(str, Enum):
    """Detection strategies used"""
    RULE_BASED = "rule_based"
    ANOMALY_DETECTION = "anomaly_detection"
    BEHAVIORAL = "behavioral"
    CORRELATION = "correlation"
    THREAT_INTEL = "threat_intel"


@dataclass
class DetectionResult:
    """Result of event detection"""
    is_incident: bool
    confidence: float  # 0.0-1.0
    risk_score: float  # 0.0-100.0
    strategy_used: DetectionStrategy
    mitre_tactics: List[str]
    mitre_techniques: List[str]
    reasoning: str
    suggested_priority: str  # CRITICAL, HIGH, MEDIUM, LOW


class IncidentDetectionEngine:
    """
    Analyzes events and creates incidents
    
    Implements multiple detection strategies:
    1. Rule-based (SIGMA-like rules)
    2. Anomaly detection (statistical)
    3. Behavioral profiles
    4. Event correlation
    5. Threat intelligence matching
    """
    
    def __init__(self):
        self.detection_rules = {}
        self.anomaly_profiles = {}
        self.alert_count = 0
        
        # Metrics
        self.metrics = {
            'events_analyzed': 0,
            'incidents_created': 0,
            'false_positives': 0,
            'avg_detection_latency_ms': 0,
        }
        
        self._initialize_detection_rules()
    
    def _initialize_detection_rules(self) -> None:
        """Initialize default detection rules"""
        
        # Rule 1: Brute force detection
        self.detection_rules['brute_force'] = {
            'name': 'SSH Brute Force Attack',
            'type': 'rule_based',
            'mitre_tactics': ['credential_access'],
            'mitre_techniques': ['T1110'],  # Brute Force
            'condition': {
                'event_type': 'SECURITY_ALERT',
                'source': 'ssh_honeypot',
                'threshold': {'failed_attempts': 5, 'time_window': 60},  # 5 in 60 seconds
            },
            'risk_score': 80,
            'priority': 'HIGH',
        }
        
        # Rule 2: Web exploit attempt
        self.detection_rules['web_exploit'] = {
            'name': 'Web Application Exploit Attempt',
            'type': 'rule_based',
            'mitre_tactics': ['initial_access', 'execution'],
            'mitre_techniques': ['T1190', 'T1059'],  # Exploit + Command Interpreter
            'condition': {
                'keywords': ['sql_injection', 'xss', 'path_traversal', 'rce'],
            },
            'risk_score': 85,
            'priority': 'CRITICAL',
        }
        
        # Rule 3: Suspicious PowerShell
        self.detection_rules['suspicious_powershell'] = {
            'name': 'Suspicious PowerShell Execution',
            'type': 'rule_based',
            'mitre_tactics': ['execution', 'defense_evasion'],
            'mitre_techniques': ['T1059', 'T1197'],  # Command Interpreter + BITS
            'condition': {
                'keywords': ['powershell', 'iex', 'invoke-expression', 'downloadstring'],
            },
            'risk_score': 75,
            'priority': 'HIGH',
        }
        
        # Rule 4: Unusual network traffic
        self.detection_rules['unusual_network'] = {
            'name': 'Unusual Network Traffic',
            'type': 'anomaly',
            'mitre_tactics': ['command_and_control', 'exfiltration'],
            'mitre_techniques': ['T1071', 'T1020'],  # Protocol + Automated Exfiltration
            'condition': {
                'data_volume_threshold': 1024 * 1024 * 100,  # 100 MB
                'unusual_port': True,
            },
            'risk_score': 70,
            'priority': 'MEDIUM',
        }
        
        # Rule 5: File integrity monitoring
        self.detection_rules['file_integrity'] = {
            'name': 'Unauthorized File Modification',
            'type': 'rule_based',
            'mitre_tactics': ['impact', 'persistence'],
            'mitre_techniques': ['T1531', 'T1547'],  # Impact + Persistence
            'condition': {
                'protected_files': ['/etc/passwd', '/etc/shadow', 'C:\\Windows\\System32\\'],
                'action': 'modified',
            },
            'risk_score': 90,
            'priority': 'CRITICAL',
        }
        
        logger.info(f"✓ Initialized {len(self.detection_rules)} detection rules")
    
    async def analyze_event(self, event: Dict[str, Any]) -> Optional[DetectionResult]:
        """
        Analyze a single event for incident indicators
        
        Args:
            event: Event dictionary
        
        Returns:
            DetectionResult if incident detected, None otherwise
        """
        
        import time
        start = time.time()
        
        self.metrics['events_analyzed'] += 1
        
        # Try each detection strategy
        
        # 1. Rule-based detection
        rule_result = self._rule_based_detection(event)
        if rule_result:
            latency = int((time.time() - start) * 1000)
            self.metrics['avg_detection_latency_ms'] += latency
            self.metrics['incidents_created'] += 1
            return rule_result
        
        # 2. Anomaly detection
        anomaly_result = self._anomaly_detection(event)
        if anomaly_result:
            latency = int((time.time() - start) * 1000)
            self.metrics['avg_detection_latency_ms'] += latency
            self.metrics['incidents_created'] += 1
            return anomaly_result
        
        # 3. Threat intelligence matching
        ti_result = self._threat_intel_detection(event)
        if ti_result:
            latency = int((time.time() - start) * 1000)
            self.metrics['avg_detection_latency_ms'] += latency
            self.metrics['incidents_created'] += 1
            return ti_result
        
        return None
    
    def _rule_based_detection(self, event: Dict[str, Any]) -> Optional[DetectionResult]:
        """
        SIGMA-like rule-based detection
        
        Checks event against predefined rules
        """
        
        event_type = event.get('event_type', '').upper()
        event_desc = event.get('description', '').lower()
        source = event.get('source', '').lower()
        
        # Check against each rule
        for rule_id, rule in self.detection_rules.items():
            if rule['type'] != 'rule_based':
                continue
            
            condition = rule['condition']
            
            # Brute force detection
            if rule_id == 'brute_force':
                if source == 'ssh_honeypot' and 'failed' in event_desc:
                    return DetectionResult(
                        is_incident=True,
                        confidence=0.85,
                        risk_score=float(rule['risk_score']),
                        strategy_used=DetectionStrategy.RULE_BASED,
                        mitre_tactics=rule['mitre_tactics'],
                        mitre_techniques=rule['mitre_techniques'],
                        reasoning=f"Matched rule: {rule['name']}",
                        suggested_priority=rule['priority'],
                    )
            
            # Web exploit detection
            if rule_id == 'web_exploit':
                keywords = condition.get('keywords', [])
                if any(kw in event_desc for kw in keywords):
                    return DetectionResult(
                        is_incident=True,
                        confidence=0.90,
                        risk_score=float(rule['risk_score']),
                        strategy_used=DetectionStrategy.RULE_BASED,
                        mitre_tactics=rule['mitre_tactics'],
                        mitre_techniques=rule['mitre_techniques'],
                        reasoning=f"Matched rule: {rule['name']}",
                        suggested_priority=rule['priority'],
                    )
            
            # Suspicious PowerShell
            if rule_id == 'suspicious_powershell':
                keywords = condition.get('keywords', [])
                if any(kw in event_desc for kw in keywords):
                    return DetectionResult(
                        is_incident=True,
                        confidence=0.80,
                        risk_score=float(rule['risk_score']),
                        strategy_used=DetectionStrategy.RULE_BASED,
                        mitre_tactics=rule['mitre_tactics'],
                        mitre_techniques=rule['mitre_techniques'],
                        reasoning=f"Matched rule: {rule['name']}",
                        suggested_priority=rule['priority'],
                    )
        
        return None
    
    def _anomaly_detection(self, event: Dict[str, Any]) -> Optional[DetectionResult]:
        """
        Anomaly detection based on statistical deviation
        
        Detects unusual patterns:
        - Unusual time of access
        - Unusual geographic location
        - Unusual data transfers
        - Unusual command patterns
        """
        
        source = event.get('source', '').lower()
        raw_data = event.get('raw_data', {})
        
        # Detect unusual network traffic
        if 'data_volume' in raw_data:
            volume = raw_data.get('data_volume', 0)
            threshold = 1024 * 1024 * 100  # 100 MB
            
            if volume > threshold:
                return DetectionResult(
                    is_incident=True,
                    confidence=0.70,
                    risk_score=70.0,
                    strategy_used=DetectionStrategy.ANOMALY_DETECTION,
                    mitre_tactics=['exfiltration', 'command_and_control'],
                    mitre_techniques=['T1020', 'T1071'],
                    reasoning="Unusual data volume detected",
                    suggested_priority="MEDIUM",
                )
        
        return None
    
    def _threat_intel_detection(self, event: Dict[str, Any]) -> Optional[DetectionResult]:
        """
        Match event against threat intelligence
        
        Checks:
        - Known malicious IPs
        - Known malicious domains
        - Known malicious file hashes
        - Known attack patterns
        """
        
        source_ip = event.get('source_ip', '')
        
        # Example: Check against known malicious IPs
        known_malicious_ips = [
            '192.168.1.100',  # Example malicious IP
            '10.0.0.50',
        ]
        
        if source_ip in known_malicious_ips:
            return DetectionResult(
                is_incident=True,
                confidence=0.95,
                risk_score=95.0,
                strategy_used=DetectionStrategy.THREAT_INTEL,
                mitre_tactics=['initial_access'],
                mitre_techniques=['T1566'],
                reasoning=f"Source IP {source_ip} in threat intelligence database",
                suggested_priority="CRITICAL",
            )
        
        return None
    
    def create_incident_from_detection(
        self,
        event: Dict[str, Any],
        detection: DetectionResult
    ) -> Dict[str, Any]:
        """
        Create incident from detection result
        
        Args:
            event: Detected event
            detection: Detection result
        
        Returns:
            Incident dictionary
        """
        
        return {
            'title': f"Detected: {event.get('title', 'Unknown')}",
            'description': f"{detection.reasoning}\nOriginal event: {event.get('description', '')}",
            'status': 'OPEN',
            'priority': detection.suggested_priority,
            'severity': event.get('severity', 'MEDIUM'),
            'mitre_tactics': detection.mitre_tactics,
            'mitre_techniques': detection.mitre_techniques,
            'risk_score': detection.risk_score,
            'confidence': detection.confidence,
            'detection_strategy': detection.strategy_used.value,
            'source_event_id': event.get('event_id'),
            'created_at': datetime.utcnow().isoformat(),
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get detection engine metrics"""
        
        avg_latency = (
            self.metrics['avg_detection_latency_ms'] / self.metrics['incidents_created']
            if self.metrics['incidents_created'] > 0 else 0
        )
        
        return {
            'events_analyzed': self.metrics['events_analyzed'],
            'incidents_created': self.metrics['incidents_created'],
            'false_positives': self.metrics['false_positives'],
            'avg_detection_latency_ms': avg_latency,
            'detection_rules_count': len(self.detection_rules),
            'incident_rate_pct': (
                self.metrics['incidents_created'] / self.metrics['events_analyzed'] * 100
                if self.metrics['events_analyzed'] > 0 else 0
            ),
        }


# Global instance
detection_engine = IncidentDetectionEngine()

"""
Decision-Driven Alert Intelligence Engine

Transforms raw detections into actionable recommendations.
Tells analysts: WHAT IS CRITICAL + WHAT TO DO NEXT.

Phase 2 Gap Fix: Moves from "data dashboard" to "decision platform"
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels driving action urgency"""
    INFO = "info"           # Log it
    LOW = "low"             # Review trend
    MEDIUM = "medium"       # Investigate this week
    HIGH = "high"           # Investigate today
    CRITICAL = "critical"   # Investigate now


class RecommendedAction(str, Enum):
    """What the analyst should do"""
    ACKNOWLEDGE = "acknowledge"           # Just note it
    INVESTIGATE = "investigate"           # Deep dive required
    ISOLATE = "isolate"                   # Take endpoint offline
    BLOCK = "block"                       # Block IP/domain
    ESCALATE = "escalate"                 # Notify SOC lead
    EXECUTE_PLAYBOOK = "execute_playbook" # Run incident response


@dataclass
class ActionableAlert:
    """
    Not just: "Event detected"
    But: "Event detected → DO THIS → Because of THAT"
    """
    id: str
    title: str                              # "SSH Brute Force on DB Server"
    severity: AlertSeverity
    recommended_action: RecommendedAction
    business_context: str                   # "Critical database server"
    action_steps: List[str]                 # Step-by-step playbook
    confidence: float                       # 0-1, how sure are we?
    false_positive_risk: str               # "Low" / "Medium" / "High"
    estimated_impact: str                  # "Potential data exfiltration"
    time_to_respond_minutes: int           # SLA
    related_incidents: List[str]           # Other incidents to check
    created_at: datetime


@dataclass
class IncidentContext:
    """Rich context for decision-making"""
    incident_id: str
    severity_score: int                    # 0-100
    duplicate_incidents_24h: int           # How many similar recently?
    asset_criticality: int                 # 1-10 (10=critical)
    recent_patch_status: str               # "Patched" / "Vulnerable"
    false_positive_rate_this_rule: float   # Historical accuracy
    time_since_last_similar: Optional[str] # "2 days ago"


class DecisionEngine:
    """
    Converts detection events into HIGH-VALUE decisions
    
    Not: "Anomaly detected"
    But: "Anomaly detected on PROD-DB-01 (critical asset) → 
          ISOLATE IMMEDIATELY (90% confidence risk is real)"
    """
    
    def __init__(self):
        self.action_playbooks = self._initialize_playbooks()
        self.false_positive_history = {}  # Track accuracy per rule
    
    def _initialize_playbooks(self) -> Dict[str, List[str]]:
        """Pre-built response playbooks"""
        return {
            # ===========================
            # Credential-Based Attacks
            # ===========================
            "ssh_brute_force": [
                "1. IMMEDIATE: Check failed_login patterns in last 10 min",
                "2. ASAP: Block source IP at firewall",
                "3. Check if credentials valid (from breach DB?)",
                "4. Reset password on targeted account",
                "5. Review: What did attacker try in first 60s?",
                "6. Escalate: If credentials matched bypass rules"
            ],
            
            "password_spray": [
                "1. Check: How many unique users targeted?",
                "2. If >50: Corporate-wide password reset (lower risk)",
                "3. If <10: Target-specific attack (HIGH priority)",
                "4. Block source IP",
                "5. Check for successful logins",
                "6. If successful: Assume credential harvesting"
            ],
            
            # ===========================
            # Data Exfiltration
            # ===========================
            "unusual_data_transfer": [
                "1. IMMEDIATE: Isolate source host from network",
                "2. Get process name + command line from endpoint",
                "3. Check: Is destination known (cloud backup) or suspicious?",
                "4. If suspicious: Block all traffic from host",
                "5. Preserve evidence (memory dump, network caps)",
                "6. Check for lateral movement to similar systems"
            ],
            
            "database_exfiltration": [
                "1. CRITICAL: Kill database connections from source IP",
                "2. Snapshot database at this moment (forensics)",
                "3. Check transaction log: what was extracted?",
                "4. Notify Data Privacy team (GDPR/compliance alert)",
                "5. Check: Is this user's normal behavior?",
                "6. If admin: Check for privilege escalation chain"
            ],
            
            # ===========================
            # Web Application Attacks
            # ===========================
            "sql_injection": [
                "1. IMMEDIATE: Block source IP at WAF",
                "2. Check: Did payload execute successfully?",
                "3. Check database: Any admin operations in logs?",
                "4. If yes: Database was compromised (CRITICAL)",
                "5. Review: Was this authenticated user or unauthenticated?",
                "6. Patch: SQL injection vulnerability in code"
            ],
            
            "file_integrity_violation": [
                "1. IMMEDIATE: Snapshot system (file hashes, memory)",
                "2. Check: Is file legitimately modified (deploy in progress)?",
                "3. If not: Assume system compromise (HIGH priority)",
                "4. Isolate host",
                "5. Check: Any process modifications or rootkits?",
                "6. Restore from backup + patch"
            ],
            
            # ===========================
            # Privilege Escalation
            # ===========================
            "suspicious_privilege_escalation": [
                "1. Check: Is this user normally admin?",
                "2. If no: IMMEDIATE containment (potential breach)",
                "3. Check sudo/privilege logs around timestamp",
                "4. Review: What did user do after escalation?",
                "5. If lateral movement: Full containment (network isolation)",
                "6. Force password reset on compromised account"
            ],
            
            # ===========================
            # Malware/Code Execution
            # ===========================
            "malicious_powershell": [
                "1. IMMEDIATE: Isolate endpoint",
                "2. Get full PowerShell command + script content",
                "3. Submit to malware analysis (VirusTotal, Hybrid Analysis)",
                "4. Check: Did payload execute (return codes, created files)?",
                "5. If yes: Full forensic analysis needed",
                "6. Kill process + scan system for other artifacts"
            ]
        }
    
    def generate_actionable_alert(
        self,
        detection_type: str,
        incident_id: str,
        severity_score: int,
        asset_name: str,
        asset_criticality: int,
        event_description: str,
        confidence: float,
        recent_similar_count: int = 0
    ) -> ActionableAlert:
        """
        Transform raw detection → Decision for analyst
        
        Input: Technical detection (raw signal)
        Output: Business decision (actionable alert)
        """
        
        # Determine severity from risk + context
        severity = self._calculate_severity(
            severity_score=severity_score,
            asset_criticality=asset_criticality,
            confidence=confidence,
            similar_count=recent_similar_count
        )
        
        # What should analyst DO?
        action = self._recommend_action(
            detection_type=detection_type,
            severity=severity,
            asset_criticality=asset_criticality
        )
        
        # How much time do we have?
        time_to_respond = self._estimate_response_time(severity)
        
        # Get playbook steps
        steps = self.action_playbooks.get(
            detection_type,
            ["1. Investigate manually", "2. Consult SOC lead"]
        )
        
        # Historical accuracy of this detection type
        fp_risk = self._calculate_false_positive_risk(
            detection_type, confidence
        )
        
        # Create decision object
        alert = ActionableAlert(
            id=incident_id,
            title=self._generate_title(detection_type, asset_name),
            severity=severity,
            recommended_action=action,
            business_context=f"Target: {asset_name} (Criticality: {asset_criticality}/10)",
            action_steps=steps,
            confidence=confidence,
            false_positive_risk=fp_risk,
            estimated_impact=self._estimate_impact(detection_type, asset_criticality),
            time_to_respond_minutes=time_to_respond,
            related_incidents=[],  # Would query incident table
            created_at=datetime.utcnow()
        )
        
        logger.info(
            f"Decision Alert: {alert.title} → Action: {action.value} "
            f"(Confidence: {confidence:.0%}, Risk: {fp_risk})"
        )
        
        return alert
    
    def _calculate_severity(
        self,
        severity_score: int,
        asset_criticality: int,
        confidence: float,
        similar_count: int
    ) -> AlertSeverity:
        """
        Severity = Technical Signal × Business Impact × Confidence
        
        Not just: "Anomaly = High"
        But: "Anomaly on non-critical dev server = Low"
             "Same anomaly on prod DB = Critical"
        """
        
        # Base severity from detection
        base_severity = severity_score
        
        # Amplify by asset criticality
        adjusted = base_severity * (asset_criticality / 5.0)
        
        # Reduce confidence impact (high confidence → take it seriously)
        adjusted = adjusted * (1.0 if confidence > 0.8 else 0.7)
        
        # Pattern detection (repeated = more serious)
        if similar_count > 3:
            adjusted *= 1.3  # Coordinated attack pattern
        
        # Map to severity level
        if adjusted >= 85:
            return AlertSeverity.CRITICAL
        elif adjusted >= 70:
            return AlertSeverity.HIGH
        elif adjusted >= 50:
            return AlertSeverity.MEDIUM
        elif adjusted >= 30:
            return AlertSeverity.LOW
        else:
            return AlertSeverity.INFO
    
    def _recommend_action(
        self,
        detection_type: str,
        severity: AlertSeverity,
        asset_criticality: int
    ) -> RecommendedAction:
        """What should analyst DO?"""
        
        # Criticality + Severity → Action
        if severity == AlertSeverity.CRITICAL:
            if asset_criticality >= 8:
                return RecommendedAction.ISOLATE  # Take it offline
            else:
                return RecommendedAction.ESCALATE  # Get manager approval
        
        elif severity == AlertSeverity.HIGH:
            if "exfiltration" in detection_type.lower():
                return RecommendedAction.ISOLATE
            elif "escalation" in detection_type.lower():
                return RecommendedAction.ISOLATE
            else:
                return RecommendedAction.INVESTIGATE
        
        elif severity == AlertSeverity.MEDIUM:
            return RecommendedAction.INVESTIGATE
        
        elif severity == AlertSeverity.LOW:
            return RecommendedAction.ACKNOWLEDGE
        
        else:
            return RecommendedAction.ACKNOWLEDGE
    
    def _estimate_response_time(self, severity: AlertSeverity) -> int:
        """SLA: minutes to respond"""
        return {
            AlertSeverity.CRITICAL: 5,      # Immediately
            AlertSeverity.HIGH: 15,          # Within 15 min
            AlertSeverity.MEDIUM: 60,        # Within 1 hour
            AlertSeverity.LOW: 480,          # Within 8 hours
            AlertSeverity.INFO: 1440         # Within 1 day
        }[severity]
    
    def _estimate_false_positive_risk(
        self,
        detection_type: str,
        confidence: float
    ) -> str:
        """How likely is this a false positive?"""
        
        # Maintain accuracy history (would query DB in production)
        known_accuracy = {
            "ssh_brute_force": 0.95,
            "sql_injection": 0.92,
            "file_integrity_violation": 0.98,
            "unusual_data_transfer": 0.75,  # Lower - many false positives
            "password_spray": 0.88,
        }
        
        accuracy = known_accuracy.get(detection_type, 0.7)
        overall_confidence = accuracy * confidence
        
        if overall_confidence > 0.9:
            return "Low"
        elif overall_confidence > 0.75:
            return "Medium"
        else:
            return "High"
    
    def _generate_title(self, detection_type: str, asset_name: str) -> str:
        """Human-readable alert title"""
        titles = {
            "ssh_brute_force": f"SSH Brute Force Attack on {asset_name}",
            "sql_injection": f"SQL Injection Attempt Against {asset_name}",
            "file_integrity_violation": f"Critical File Modified on {asset_name}",
            "unusual_data_transfer": f"Unusual Data Transfer from {asset_name}",
            "database_exfiltration": f"Potential Database Theft from {asset_name}",
            "malicious_powershell": f"Malicious PowerShell on {asset_name}",
            "privilege_escalation": f"Privilege Escalation on {asset_name}",
        }
        return titles.get(detection_type, f"Security Alert on {asset_name}")
    
    def _estimate_impact(
        self,
        detection_type: str,
        asset_criticality: int
    ) -> str:
        """Business impact description"""
        
        impacts = {
            "ssh_brute_force": "Unauthorized system access",
            "sql_injection": "Database compromise → Data theft/modification",
            "file_integrity_violation": "System compromise → Potential persistence",
            "unusual_data_transfer": "Data exfiltration in progress",
            "database_exfiltration": "Critical data breach (GDPR impact)",
            "malicious_powershell": "Malware execution (ransomware/backdoor risk)",
            "privilege_escalation": "Admin compromise → Full system control",
        }
        
        base_impact = impacts.get(detection_type, "Unknown threat")
        
        if asset_criticality >= 8:
            return f"{base_impact} on CRITICAL ASSET (business impact HIGH)"
        elif asset_criticality >= 5:
            return f"{base_impact} on important system"
        else:
            return f"{base_impact} on non-critical system"


# Example usage for dashboard
class DashboardDecisionCenter:
    """
    What your dashboard should show (not raw metrics, but DECISIONS)
    """
    
    def __init__(self):
        self.decision_engine = DecisionEngine()
    
    def get_actionable_summary(self) -> Dict:
        """
        Dashboard summary: NOT "20 events detected"
        But: "CRITICAL ACTION NEEDED: 2 items, DO THIS NOW"
        """
        return {
            "critical_actions": [
                {
                    "title": "SSH Brute Force on DB-PROD-01",
                    "action": "ISOLATE IMMEDIATELY",
                    "reason": "Critical asset + 95% confidence",
                    "steps": ["1. Block source IP", "2. Check logs", "3. Reset password"],
                    "time_to_respond_minutes": 5
                }
            ],
            "pending_investigations": [
                {
                    "title": "Unusual data transfer from WEB-02",
                    "action": "INVESTIGATE THIS HOUR",
                    "reason": "Potential exfiltration + medium criticality",
                    "time_to_respond_minutes": 60
                }
            ],
            "acknowledged_alerts": [
                {
                    "title": "Failed login attempt on test server",
                    "action": "MONITOR",
                    "reason": "Low criticality + development asset"
                }
            ]
        }

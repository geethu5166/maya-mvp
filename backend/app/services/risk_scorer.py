"""
Advanced risk scoring algorithm
CVSS-inspired with additional factors:
- Severity of impact
- Exploitability
- Business context
- Threat intelligence
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(str, Enum):
    """Risk severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RiskScorer:
    """
    Multi-factor risk scoring system (0-100)
    Provides nuanced threat assessment beyond simple severity
    """
    
    def __init__(self):
        """Initialize risk scorer"""
        self.logger = logger
    
    async def calculate_risk_score(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive risk score for a security event
        
        Args:
            event: Security event data
            
        Returns:
            Risk assessment with score and level
        """
        try:
            # Base score calculation
            base_score = self._calculate_base_score(event)
            
            # Apply modifiers
            modifier = self._calculate_modifiers(event)
            final_score = min(100, max(0, base_score + modifier))
            
            # Determine risk level
            risk_level = self._score_to_level(final_score)
            
            return {
                "risk_score": final_score,
                "risk_level": risk_level,
                "base_score": base_score,
                "modifier": modifier,
                "recommendation": self._get_recommendation(final_score)
            }
        except Exception as e:
            self.logger.error(f"Error calculating risk score: {e}")
            return {
                "error": str(e),
                "risk_score": 0,
                "risk_level": RiskLevel.INFO
            }
    
    def _calculate_base_score(self, event: Dict[str, Any]) -> float:
        """Calculate base risk score from event attributes"""
        base_score = 50  # Default middle score
        
        # Adjust based on event type
        event_type = event.get("event_type", "").lower()
        if "malware" in event_type:
            base_score = 85
        elif "unauthorized_access" in event_type:
            base_score = 80
        elif "suspicious" in event_type:
            base_score = 60
        
        return base_score
    
    def _calculate_modifiers(self, event: Dict[str, Any]) -> float:
        """Calculate score modifiers based on context"""
        modifier = 0
        
        # Modifier based on affected assets
        if event.get("is_critical_asset"):
            modifier += 15
        
        # Modifier based on user sensitivity
        if event.get("involves_admin"):
            modifier += 10
        
        # Modifier based on repeatability
        if event.get("repeat_count", 0) > 3:
            modifier += 5
        
        return modifier
    
    def _score_to_level(self, score: float) -> str:
        """Convert numerical score to risk level"""
        if score >= 90:
            return RiskLevel.CRITICAL
        elif score >= 70:
            return RiskLevel.HIGH
        elif score >= 50:
            return RiskLevel.MEDIUM
        elif score >= 30:
            return RiskLevel.LOW
        else:
            return RiskLevel.INFO
    
    def _get_recommendation(self, score: float) -> str:
        """Get security recommendation based on score"""
        if score >= 90:
            return "Immediate investigation and containment required"
        elif score >= 70:
            return "Urgent review and escalation needed"
        elif score >= 50:
            return "Monitor closely and investigate further"
        elif score >= 30:
            return "Log for reference and monitor trends"
        else:
            return "Normal operations, maintain logging"
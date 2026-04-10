"""
Advanced AI/ML engine with:
- Threat analysis models
- Incident report generation
- Attack prediction based on patterns
- Adaptive learning from events
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import json

logger = logging.getLogger(__name__)


class AIEngineService:
    """
    Advanced AI engine for threat analysis and incident reporting
    """
    
    def __init__(self, openai_key: Optional[str] = None):
        """Initialize AI engine service"""
        self.openai_key = openai_key
        self.logger = logger
        self.attack_patterns = defaultdict(list)
        self.attacker_profiles = {}
    
    def get_threat_level(self, event: Dict[str, Any]) -> Tuple[str, float]:
        """
        Determine threat level based on event characteristics
        
        Returns:
            (threat_level, confidence)
        """
        severity = event.get('severity', 'LOW')
        event_type = event.get('type', 'UNKNOWN')
        
        # Base threat score
        severity_scores = {
            'CRITICAL': 0.95,
            'HIGH': 0.75,
            'MEDIUM': 0.50,
            'LOW': 0.30
        }
        
        threat_score = severity_scores.get(severity, 0.40)
        
        # Adjust based on event type patterns
        critical_patterns = ['SSH_BRUTE_FORCE', 'WEB_CREDENTIAL_HARVEST', 'DB_LOGIN_ATTEMPT']
        if event_type in critical_patterns:
            threat_score = max(threat_score, 0.75)
        
        # Check if attacker is known/repeat offender
        attacker_ip = event.get('attacker_ip', '')
        if attacker_ip in self.attacker_profiles:
            profile = self.attacker_profiles[attacker_ip]
            # Repeat offenders = higher threat
            threat_score = min(0.99, threat_score + (profile.get('attack_count', 0) * 0.05))
        
        # Map score to threat level
        if threat_score >= 0.85:
            threat_level = "CRITICAL"
        elif threat_score >= 0.65:
            threat_level = "HIGH"
        elif threat_score >= 0.45:
            threat_level = "MEDIUM"
        else:
            threat_level = "LOW"
        
        confidence = min(0.99, threat_score + 0.10)
        
        return threat_level, confidence
    
    async def analyze_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze security event using intelligent heuristics
        
        Args:
            event: Security event data
            
        Returns:
            AI analysis results with threat assessment
        """
        try:
            # Get threat assessment
            threat_level, confidence = self.get_threat_level(event)
            
            # Track event patterns
            event_type = event.get('type', 'UNKNOWN')
            self.attack_patterns[event_type].append({
                'timestamp': event.get('timestamp'),
                'ip': event.get('attacker_ip'),
                'severity': event.get('severity')
            })
            
            # Track attacker profile
            attacker_ip = event.get('attacker_ip', '')
            if attacker_ip not in self.attacker_profiles:
                self.attacker_profiles[attacker_ip] = {
                    'first_seen': event.get('timestamp'),
                    'attack_count': 0,
                    'attack_types': set()
                }
            
            profile = self.attacker_profiles[attacker_ip]
            profile['attack_count'] += 1
            profile['attack_types'].add(event_type)
            profile['last_seen'] = event.get('timestamp')
            
            # Generate specific recommendations
            recommendations = self._generate_recommendations(event, threat_level)
            
            # Create analysis response
            analysis = {
                "threat_level": threat_level,
                "confidence": round(confidence, 2),
                "event_type": event_type,
                "timestamp": datetime.now().isoformat(),
                "attacker_ip": attacker_ip,
                "attacker_history": {
                    "attack_count": profile.get('attack_count', 1),
                    "attack_types": list(profile.get('attack_types', set())),
                    "first_seen": profile.get('first_seen'),
                    "last_seen": profile.get('last_seen')
                },
                "summary": f"{threat_level} threat detected: {self._summarize_event(event)}",
                "recommendations": recommendations
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing event: {e}")
            return {
                "error": str(e),
                "threat_level": "UNKNOWN",
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_recommendations(self, event: Dict[str, Any], threat_level: str) -> List[str]:
        """Generate security recommendations based on event"""
        recommendations = []
        
        attacker_ip = event.get('attacker_ip')
        event_type = event.get('type')
        
        # IP-based recommendations
        if threat_level in ['CRITICAL', 'HIGH']:
            recommendations.append(f"Block IP {attacker_ip} immediately")
        
        # Event type recommendations
        if event_type == 'SSH_BRUTE_FORCE':
            recommendations.append("Enable SSH key-based auth only")
            recommendations.append("Implement fail2ban or similar")
            recommendations.append("Rotate SSH host keys")
        
        elif event_type == 'WEB_CREDENTIAL_HARVEST':
            recommendations.append("Review user accounts for compromise")
            recommendations.append("Enforce password reset")
            recommendations.append("Enable MFA")
        
        elif event_type == 'DB_LOGIN_ATTEMPT':
            recommendations.append("Isolate database server")
            recommendations.append("Review database access logs")
            recommendations.append("Change database credentials")
        
        # Pattern-based
        if event.get('attacker_ip') in self.attacker_profiles:
            profile = self.attacker_profiles[event['attacker_ip']]
            if profile['attack_count'] > 5:
                recommendations.append("This is a persistent attacker - escalate to SOC")
        
        return recommendations[:3]  # Return top 3 recommendations
    
    def _summarize_event(self, event: Dict[str, Any]) -> str:
        """Create human-readable event summary"""
        event_type = event.get('type', 'UNKNOWN')
        ip = event.get('attacker_ip', 'unknown')
        
        summaries = {
            'SSH_BRUTE_FORCE': f"SSH brute force attack from {ip}",
            'WEB_CREDENTIAL_HARVEST': f"Web credential harvest attempt from {ip}",
            'DB_LOGIN_ATTEMPT': f"Database login attempt from {ip}",
            'WEB_RECON': f"Web reconnaissance scan from {ip}",
            'WEB_SCAN': f"Web vulnerability scan from {ip}",
        }
        
        return summaries.get(event_type, f"Security event from {ip}")
    
    async def generate_incident_report(self, events: List[Dict[str, Any]]) -> str:
        """
        Generate comprehensive incident report from events
        
        Args:
            events: List of security events
            
        Returns:
            Formatted incident report
        """
        try:
            if not events:
                return "No events to report"
            
            # Analyze events
            event_types = Counter(e.get('type') for e in events)
            attackers = Counter(e.get('attacker_ip') for e in events)
            severities = Counter(e.get('severity') for e in events)
            
            # Build report
            report_lines = [
                "=" * 60,
                "MAYA SOC - INCIDENT REPORT",
                "=" * 60,
                f"Generated: {datetime.now().isoformat()}",
                f"Report Period: {len(events)} security events",
                "",
                "SUMMARY",
                "-" * 60,
                f"Total Events: {len(events)}",
                f"Unique Attackers: {len(attackers)}",
                f"Critical Events: {severities.get('CRITICAL', 0)}",
                f"High Events: {severities.get('HIGH', 0)}",
                "",
                "ATTACK TYPES",
                "-" * 60,
            ]
            
            for attack_type, count in event_types.most_common(5):
                report_lines.append(f"  {attack_type}: {count} attacks")
            
            report_lines.extend([
                "",
                "TOP ATTACKERS",
                "-" * 60,
            ])
            
            for attacker_ip, count in attackers.most_common(5):
                report_lines.append(f"  {attacker_ip}: {count} attacks")
            
            report_lines.extend([
                "",
                "RECOMMENDATIONS",
                "-" * 60,
                "1. Block top attacker IPs at firewall",
                "2. Review and strengthen authentication",
                "3. Enable additional logging on compromised systems",
                "4. Deploy additional honeypots on high-risk networks",
                "",
                "=" * 60,
            ])
            
            return "\n".join(report_lines)
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            return f"Error generating report: {e}"
    
    async def predict_attacks(self, historical_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Predict potential future attacks based on historical data patterns
        
        Args:
            historical_data: Historical security event data
            
        Returns:
            List of predicted attack scenarios with probabilities
        """
        try:
            predictions = []
            
            if not historical_data:
                return predictions
            
            # Analyze attack patterns
            event_types = Counter(e.get('type') for e in historical_data)
            time_based_attacks = defaultdict(int)
            
            # Analyze time patterns
            for event in historical_data:
                try:
                    timestamp = event.get('timestamp', '')
                    if timestamp:
                        hour = int(timestamp.split('T')[1].split(':')[0])
                        time_based_attacks[hour] += 1
                except:
                    pass
            
            # Predict based on most common attack types
            for attack_type, count in event_types.most_common(3):
                probability = min(0.95, (count / max(1, len(historical_data))) + 0.2)
                
                predictions.append({
                    "predicted_attack_type": attack_type,
                    "probability": round(probability, 2),
                    "confidence": round(min(0.9, count / 100), 2),
                    "timeframe": "next_24_hours",
                    "recommendation": f"Prepare defenses for {attack_type}"
                })
            
            # If no predictions yet, suggest based on historical data
            if not predictions and event_types:
                most_common = event_types.most_common(1)[0][0]
                predictions.append({
                    "predicted_attack_type": most_common,
                    "probability": 0.65,
                    "confidence": 0.5,
                    "timeframe": "next_7_days",
                    "recommendation": f"Monitor for {most_common} attacks"
                })
            
            return predictions
            
        except Exception as e:
            self.logger.error(f"Error predicting attacks: {e}")
            return []
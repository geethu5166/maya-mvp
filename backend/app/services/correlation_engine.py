"""
Advanced Correlation Engine

Links related security events into attack chains
Detects multi-event patterns and attack progressions

Phase 3: Advanced Correlation
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class CorrelationType(str, Enum):
    """Types of event correlations"""
    SAME_USER = "same_user"              # Same username across events
    SAME_ASSET = "same_asset"            # Same server/database/file
    SAME_SOURCE_IP = "same_source_ip"    # Same attacker IP
    SAME_TIME_WINDOW = "same_time_window"  # Events within seconds
    ESCALATION = "escalation"            # Failed attempt → success
    ATTACK_CHAIN = "attack_chain"        # Multi-step attack pattern
    RECONNAISSANCE = "reconnaissance"    # Probing behavior
    LATERAL_MOVEMENT = "lateral_movement"  # After initial compromise


@dataclass
class CorrelatedEvent:
    """An event with correlation metadata"""
    event_id: str
    event_type: str                    # "ssh_brute", "unusual_transfer", etc.
    severity: int                       # 0-100
    timestamp: datetime
    user: Optional[str]
    asset: Optional[str]
    source_ip: Optional[str]
    details: Dict
    
    # Correlation fields
    correlated_with: List[str] = field(default_factory=list)  # Event IDs
    correlation_types: List[CorrelationType] = field(default_factory=list)
    is_part_of_chain: bool = False
    chain_id: Optional[str] = None


@dataclass
class AttackChain:
    """Multi-step attack progression"""
    chain_id: str
    chain_type: str                    # "brute_force_to_data_exfil", etc.
    severity: int                       # Aggregated severity (higher for chains)
    events: List[str]                  # Event IDs in sequence
    start_time: datetime
    end_time: datetime
    user: Optional[str]
    assets: Set[str]
    source_ips: Set[str]
    confidence: float                  # 0-1 likelihood of actual chain
    attack_stages: List[str]           # ["reconnaissance", "exploitation", "exfiltration"]
    reasoning: str
    
    def duration_seconds(self) -> int:
        return int((self.end_time - self.start_time).total_seconds())


class PatternMatcher:
    """
    Detects specific attack patterns
    """
    
    # Pattern definitions: (sequence of event types, description)
    KNOWN_PATTERNS = {
        "brute_force_compromise": [
            "ssh_brute_force",
            "successful_login",
            "suspicious_process_execution"
        ],
        "data_exfiltration": [
            "unusual_database_query",
            "large_data_transfer",
            "connection_to_external_ip"
        ],
        "lateral_movement": [
            "successful_login",
            "privilege_escalation",
            "admin_command_execution",
            "database_access"
        ],
        "reconnaissance": [
            "port_scanning",
            "service_enumeration",
            "vulnerability_scanning"
        ]
    }
    
    @staticmethod
    def check_pattern(
        events: List[CorrelatedEvent],
        pattern_name: str
    ) -> Tuple[bool, float]:
        """
        Check if events match a known pattern
        
        Returns: (matches, confidence)
        """
        
        pattern = PatternMatcher.KNOWN_PATTERNS.get(pattern_name)
        if not pattern:
            return False, 0.0
        
        event_types = [e.event_type for e in events]
        
        # Simple sequence matching
        matches = 0
        for pattern_event in pattern:
            if pattern_event in event_types:
                matches += 1
        
        confidence = matches / len(pattern)
        return matches >= len(pattern) * 0.7, confidence
    
    @staticmethod
    def detect_escalation(
        events: List[CorrelatedEvent]
    ) -> Tuple[bool, Optional[str]]:
        """
        Detect escalation pattern:
        Failed attempts followed by successful access
        """
        
        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        for i in range(len(sorted_events) - 1):
            current = sorted_events[i]
            next_event = sorted_events[i + 1]
            
            # Check for failure → success pattern
            if (("brute_force" in current.event_type or "failed" in current.event_type) and
                ("successful_login" in next_event.event_type or "access" in next_event.event_type)):
                
                # Check if close in time (within 5 minutes)
                time_diff = (next_event.timestamp - current.timestamp).total_seconds()
                if time_diff < 300:
                    return True, f"Escalation detected: {current.event_type} → {next_event.event_type}"
        
        return False, None


class EventCorrelator:
    """
    Correlates individual events to find relationships
    """
    
    def __init__(self, time_window_seconds: int = 300):
        """
        time_window_seconds: Events within this window are candidates for correlation
        """
        self.time_window = timedelta(seconds=time_window_seconds)
        self.events: Dict[str, CorrelatedEvent] = {}
    
    def add_event(
        self,
        event_id: str,
        event_type: str,
        severity: int,
        timestamp: datetime,
        user: Optional[str] = None,
        asset: Optional[str] = None,
        source_ip: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> CorrelatedEvent:
        """Add event and correlate with existing events"""
        
        event = CorrelatedEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=timestamp,
            user=user,
            asset=asset,
            source_ip=source_ip,
            details=details or {}
        )
        
        self.events[event_id] = event
        
        # Find correlations with existing events
        self._correlate_event(event)
        
        return event
    
    def _correlate_event(self, event: CorrelatedEvent):
        """Find all correlations for this event"""
        
        for other_id, other_event in self.events.items():
            if other_id == event.event_id:
                continue
            
            # Check if within time window
            time_diff = abs((event.timestamp - other_event.timestamp).total_seconds())
            if time_diff > self.time_window.total_seconds():
                continue
            
            # Check correlation types
            correlation_reasons = []
            
            if event.user and event.user == other_event.user:
                correlation_reasons.append(CorrelationType.SAME_USER)
            
            if event.asset and event.asset == other_event.asset:
                correlation_reasons.append(CorrelationType.SAME_ASSET)
            
            if event.source_ip and event.source_ip == other_event.source_ip:
                correlation_reasons.append(CorrelationType.SAME_SOURCE_IP)
            
            if time_diff < 60:  # Within 1 minute
                correlation_reasons.append(CorrelationType.SAME_TIME_WINDOW)
            
            # Add bidirectional correlation
            if correlation_reasons:
                event.correlated_with.append(other_id)
                event.correlation_types.extend(correlation_reasons)
                
                other_event.correlated_with.append(event.event_id)
                other_event.correlation_types.extend(correlation_reasons)
    
    def get_correlated_cluster(self, event_id: str) -> List[CorrelatedEvent]:
        """Get all events correlated with a given event (transitive closure)"""
        
        if event_id not in self.events:
            return []
        
        visited = set()
        to_visit = [event_id]
        cluster = []
        
        while to_visit:
            current_id = to_visit.pop(0)
            if current_id in visited:
                continue
            
            visited.add(current_id)
            event = self.events[current_id]
            cluster.append(event)
            
            # Add all correlated events
            to_visit.extend([
                eid for eid in event.correlated_with
                if eid not in visited
            ])
        
        return cluster
    
    def get_all_clusters(self) -> List[List[CorrelatedEvent]]:
        """Get all distinct correlation clusters"""
        
        visited = set()
        clusters = []
        
        for event_id in self.events.keys():
            if event_id in visited:
                continue
            
            cluster = self.get_correlated_cluster(event_id)
            if cluster:
                clusters.append(cluster)
                visited.update(e.event_id for e in cluster)
        
        return clusters


class AttackChainDetector:
    """
    Detects multi-step attacks and chains them together
    """
    
    def __init__(self):
        self.chains: Dict[str, AttackChain] = {}
        self.event_to_chain: Dict[str, str] = {}  # event_id → chain_id
    
    def detect_chains(
        self,
        events: List[CorrelatedEvent]
    ) -> List[AttackChain]:
        """
        Analyze event cluster and detect attack chains
        """
        
        if len(events) < 2:
            return []
        
        detected_chains = []
        
        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        # Try to match known patterns
        for pattern_name in PatternMatcher.KNOWN_PATTERNS.keys():
            matches, confidence = PatternMatcher.check_pattern(sorted_events, pattern_name)
            
            if matches and confidence > 0.5:
                chain_id = f"chain_{pattern_name}_{sorted_events[0].timestamp.timestamp()}"
                
                chain = AttackChain(
                    chain_id=chain_id,
                    chain_type=pattern_name,
                    severity=min(100, int(sum(e.severity for e in sorted_events) / len(sorted_events) * 1.5)),
                    events=[e.event_id for e in sorted_events],
                    start_time=sorted_events[0].timestamp,
                    end_time=sorted_events[-1].timestamp,
                    user=sorted_events[0].user,
                    assets={e.asset for e in sorted_events if e.asset},
                    source_ips={e.source_ip for e in sorted_events if e.source_ip},
                    confidence=confidence,
                    attack_stages=self._infer_attack_stages(pattern_name),
                    reasoning=f"Pattern '{pattern_name}' detected with {confidence:.0%} confidence"
                )
                
                detected_chains.append(chain)
                self.chains[chain_id] = chain
                
                # Mark events as part of chain
                for event in sorted_events:
                    event.is_part_of_chain = True
                    event.chain_id = chain_id
                    self.event_to_chain[event.event_id] = chain_id
        
        # Check for escalation patterns
        escalation, desc = PatternMatcher.detect_escalation(sorted_events)
        if escalation:
            chain_id = f"chain_escalation_{sorted_events[0].timestamp.timestamp()}"
            
            chain = AttackChain(
                chain_id=chain_id,
                chain_type="escalation",
                severity=max(e.severity for e in sorted_events),
                events=[e.event_id for e in sorted_events],
                start_time=sorted_events[0].timestamp,
                end_time=sorted_events[-1].timestamp,
                user=sorted_events[0].user,
                assets={e.asset for e in sorted_events if e.asset},
                source_ips={e.source_ip for e in sorted_events if e.source_ip},
                confidence=0.85,
                attack_stages=["exploitation", "access_gained"],
                reasoning=desc or "Escalation pattern detected"
            )
            
            detected_chains.append(chain)
            self.chains[chain_id] = chain
        
        return detected_chains
    
    def _infer_attack_stages(self, pattern_name: str) -> List[str]:
        """Infer attack stages from pattern type"""
        
        stages_map = {
            "reconnaissance": ["reconnaissance"],
            "brute_force_compromise": ["exploitation", "access_gained", "post_exploitation"],
            "data_exfiltration": ["exfiltration"],
            "lateral_movement": ["lateral_movement", "privilege_escalation"],
        }
        
        return stages_map.get(pattern_name, ["unknown"])


class CorrelationEngine:
    """
    Main orchestrator for event correlation
    
    Combines:
    - EventCorrelator: Links individual events
    - AttackChainDetector: Finds attack chains
    - PatternMatcher: Detects known patterns
    """
    
    def __init__(self, time_window_seconds: int = 300):
        self.correlator = EventCorrelator(time_window_seconds)
        self.detector = AttackChainDetector()
    
    def process_event(
        self,
        event_id: str,
        event_type: str,
        severity: int,
        timestamp: datetime,
        user: Optional[str] = None,
        asset: Optional[str] = None,
        source_ip: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> Dict:
        """
        Process new event and return correlation analysis
        """
        
        logger.info(f"Processing event {event_id}: {event_type}")
        
        # Add event and find correlations
        event = self.correlator.add_event(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=timestamp,
            user=user,
            asset=asset,
            source_ip=source_ip,
            details=details
        )
        
        # Get correlated cluster
        cluster = self.correlator.get_correlated_cluster(event_id)
        
        result = {
            "event_id": event_id,
            "correlated_event_count": len(cluster) - 1,  # Exclude self
            "correlated_with": event.correlated_with,
            "correlation_types": [ct.value for ct in event.correlation_types],
            "attack_chains": []
        }
        
        # Detect attack chains if cluster has multiple events
        if len(cluster) > 1:
            chains = self.detector.detect_chains(cluster)
            result["attack_chains"] = [
                {
                    "chain_id": chain.chain_id,
                    "chain_type": chain.chain_type,
                    "severity": chain.severity,
                    "event_count": len(chain.events),
                    "duration_seconds": chain.duration_seconds(),
                    "confidence": chain.confidence,
                    "attack_stages": chain.attack_stages,
                    "reasoning": chain.reasoning,
                    "user": chain.user,
                    "assets": list(chain.assets),
                    "source_ips": list(chain.source_ips)
                }
                for chain in chains
            ]
        
        return result
    
    def get_correlation_summary(self) -> Dict:
        """Get summary of all correlations"""
        
        clusters = self.correlator.get_all_clusters()
        
        return {
            "total_events": len(self.correlator.events),
            "total_clusters": len(clusters),
            "single_event_clusters": sum(1 for c in clusters if len(c) == 1),
            "multi_event_clusters": sum(1 for c in clusters if len(c) > 1),
            "total_chains": len(self.detector.chains),
            "chains_by_type": self._group_chains_by_type()
        }
    
    def _group_chains_by_type(self) -> Dict[str, int]:
        """Count chains by type"""
        
        counts = {}
        for chain in self.detector.chains.values():
            counts[chain.chain_type] = counts.get(chain.chain_type, 0) + 1
        
        return counts
    
    def get_timeline(self, cluster_id: Optional[str] = None) -> List[Dict]:
        """Get chronological timeline of correlations"""
        
        if cluster_id:
            events = self.correlator.get_correlated_cluster(cluster_id)
        else:
            events = list(self.correlator.events.values())
        
        timeline = []
        for event in sorted(events, key=lambda e: e.timestamp):
            timeline.append({
                "timestamp": event.timestamp.isoformat(),
                "event_id": event.event_id,
                "event_type": event.event_type,
                "severity": event.severity,
                "user": event.user,
                "asset": event.asset,
                "source_ip": event.source_ip,
                "chain_id": event.chain_id,
                "chain_type": self.detector.chains.get(event.chain_id).chain_type if event.chain_id else None
            })
        
        return timeline

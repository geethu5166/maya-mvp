"""
Behavioral Detection Engine

Detects WHAT USER/SYSTEM NORMALLY DOES vs. ANOMALIES
Beyond rule-based (if payload contains 'xp_cmdshell' → malicious)
Into behavioral (user never transfers that much data at 3am from that location)

Phase 2 Gap Fix: Adds intelligent pattern detection
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
from statistics import mean, stdev

logger = logging.getLogger(__name__)


class BehaviorAnomalyType(str, Enum):
    """Types of behavioral anomalies"""
    TIME_BASED = "time_based"               # Unusual time of day
    VOLUME_BASED = "volume_based"           # Unusual amount
    FREQUENCY_BASED = "frequency_based"     # Unusual pattern
    LOCATION_BASED = "location_based"       # Unusual geography
    PEER_COMPARISON = "peer_comparison"     # Different from similar users
    PATTERN_BREAK = "pattern_break"         # Deviation from history


@dataclass
class UserBehaviorProfile:
    """What is this user's NORMAL behavior?"""
    user_id: str
    timestamp: datetime
    
    # Login patterns
    typical_login_hours: List[int]          # 9am-5pm usually
    typical_login_days: List[str]           # Mon-Fri usually
    login_frequency_per_day: float          # 1.5 times per day average
    
    # Access patterns
    typical_access_locations: List[str]     # "Office", "Home"
    typical_protocols: List[str]            # ["SSH", "RDP"]
    
    # Data access patterns
    daily_data_volume_mb: float             # Average data touched per day
    max_data_transfer_session_mb: float     # Never transferred >1000MB
    typical_file_types: List[str]           # ["CSV", "JSON"]
    typical_databases: List[str]            # [DB1, DB2]
    
    # Activity patterns
    commands_per_session: float             # Average command count
    typical_durations_minutes: float        # Typical session length
    
    # Privilege patterns
    uses_sudo: bool = False
    sudo_frequency_daily: float = 0.0       # How often uses sudo
    uses_admin: bool = False


@dataclass
class BehavioralAnomaly:
    """When behavior deviates from profile"""
    user_id: str
    anomaly_type: BehaviorAnomalyType
    severity_score: float                   # 0-100 (100 = extreme anomaly)
    deviation_percentage: float             # How far from normal (50% = 50% above normal)
    description: str                        # "User accessing 10x normal data volume"
    expected_behavior: str                  # "Typically 100MB/day"
    observed_behavior: str                  # "Transferred 1000MB in one session"
    risk_indicators: List[str]              # ["Combined with off-hours", "From new location"]
    timestamp: datetime


class BehavioralDetectionEngine:
    """
    Learns NORMAL behavior, detects ABNORMAL
    
    Not: "File accessed" → Actionable
    But: "User NEVER works 3am + NEVER from China
         Now accessing classified files 3am from China → CRITICAL"
    """
    
    def __init__(self):
        self.user_profiles: Dict[str, UserBehaviorProfile] = {}
        self.historical_sessions = {}  # To build profiles
        
        # Thresholds for anomaly detection
        self.volume_threshold_sigma = 2.5   # 2.5 std devs = high confidence anomaly
        self.time_anomaly_threshold = 0.8   # If 80% diff from normal
    
    def build_user_profile(
        self,
        user_id: str,
        historical_events: List[Dict],
        days_history: int = 30
    ) -> UserBehaviorProfile:
        """
        Learn what USER normally does from 30 days of history
        """
        
        # Extract patterns from events
        login_times = [e['hour'] for e in historical_events if e['event_type'] == 'login']
        login_days = [e['day'] for e in historical_events if e['event_type'] == 'login']
        
        data_transfers = [
            e['size_mb'] for e in historical_events
            if e['event_type'] == 'data_transfer'
        ]
        
        locations = [
            e['location'] for e in historical_events
            if e.get('location')
        ]
        
        # Calculate statistics
        profile = UserBehaviorProfile(
            user_id=user_id,
            timestamp=datetime.utcnow(),
            
            # TIMES: When is this user active?
            typical_login_hours=list(set(login_times)) if login_times else list(range(9, 18)),
            typical_login_days=list(set(login_days)) if login_days else ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            login_frequency_per_day=len([e for e in historical_events if e['event_type'] == 'login']) / days_history,
            
            # LOCATIONS: Where does user normally access from?
            typical_access_locations=list(set(locations)) if locations else ['Office'],
            typical_protocols=['SSH', 'RDP'],
            
            # DATA: What data does user typically access?
            daily_data_volume_mb=mean(data_transfers) if data_transfers else 100.0,
            max_data_transfer_session_mb=max(data_transfers) if data_transfers else 500.0,
            typical_file_types=['CSV', 'JSON', 'LOG'],
            typical_databases=['MongoDBMain', 'PostgresAnalytics'],
            
            # ACTIVITY: What does user do?
            commands_per_session=15.0,
            typical_durations_minutes=45.0
        )
        
        self.user_profiles[user_id] = profile
        logger.info(f"Profile built for {user_id}: login_hours={profile.typical_login_hours}")
        
        return profile
    
    def detect_behavioral_anomalies(
        self,
        user_id: str,
        event: Dict,
        profile: Optional[UserBehaviorProfile] = None
    ) -> List[BehavioralAnomaly]:
        """
        Check: Does this event fit user's normal behavior?
        """
        
        if not profile:
            profile = self.user_profiles.get(user_id)
        
        if not profile:
            return []  # No profile = can't detect anomalies yet
        
        anomalies = []
        
        # 1. TIME-BASED: Working at unusual hours?
        time_anomaly = self._check_time_anomaly(user_id, event, profile)
        if time_anomaly:
            anomalies.append(time_anomaly)
        
        # 2. VOLUME-BASED: Unusual amount of data?
        volume_anomaly = self._check_volume_anomaly(user_id, event, profile)
        if volume_anomaly:
            anomalies.append(volume_anomaly)
        
        # 3. LOCATION-BASED: Impossible travel? Unusual geography?
        location_anomaly = self._check_location_anomaly(user_id, event, profile)
        if location_anomaly:
            anomalies.append(location_anomaly)
        
        # 4. FREQUENCY-BASED: Doing actions more often than usual?
        frequency_anomaly = self._check_frequency_anomaly(user_id, event, profile)
        if frequency_anomaly:
            anomalies.append(frequency_anomaly)
        
        # 5. PATTERN-BREAK: Accessing systems user never touches?
        pattern_anomaly = self._check_pattern_break(user_id, event, profile)
        if pattern_anomaly:
            anomalies.append(pattern_anomaly)
        
        return anomalies
    
    def _check_time_anomaly(
        self,
        user_id: str,
        event: Dict,
        profile: UserBehaviorProfile
    ) -> Optional[BehavioralAnomaly]:
        """
        Is user working at weird hours?
        
        Example: User never works after 6pm, found accessing DB at 3am = suspicious
        """
        
        event_hour = event.get('hour', 12)
        is_weekend = event.get('day') in ['Sat', 'Sun']
        
        # Check: Is this hour outside normal range?
        if event_hour not in profile.typical_login_hours:
            
            # Calculate severity
            hours_away_from_normal = min(
                abs(event_hour - min(profile.typical_login_hours)),
                abs(event_hour - max(profile.typical_login_hours))
            )
            severity = min(100, hours_away_from_normal * 10)  # Each hour away = 10 points
            
            return BehavioralAnomaly(
                user_id=user_id,
                anomaly_type=BehaviorAnomalyType.TIME_BASED,
                severity_score=severity,
                deviation_percentage=(hours_away_from_normal / 12) * 100,
                description=f"User working {hours_away_from_normal} hours outside normal pattern",
                expected_behavior=f"Typical hours: {min(profile.typical_login_hours)}-{max(profile.typical_login_hours)}",
                observed_behavior=f"Active at hour {event_hour}",
                risk_indicators=[
                    "Off-hours access often precedes exfiltration",
                    "Reduced audit trail coverage (night shift staff lighter)"
                ] if hours_away_from_normal > 3 else [],
                timestamp=datetime.utcnow()
            )
        
        return None
    
    def _check_volume_anomaly(
        self,
        user_id: str,
        event: Dict,
        profile: UserBehaviorProfile
    ) -> Optional[BehavioralAnomaly]:
        """
        Is user transferring ABNORMAL amounts of data?
        
        Example: User normally transfers 50MB/day, suddenly 5000MB = insider threat indicator
        """
        
        transferred_mb = event.get('size_mb', 0)
        
        # Compare to user's history
        if transferred_mb > profile.max_data_transfer_session_mb * 5:  # 5x larger than ever
            
            severity = min(100, (transferred_mb / profile.max_data_transfer_session_mb) * 20)
            
            return BehavioralAnomaly(
                user_id=user_id,
                anomaly_type=BehaviorAnomalyType.VOLUME_BASED,
                severity_score=severity,
                deviation_percentage=((transferred_mb - profile.max_data_transfer_session_mb) / profile.max_data_transfer_session_mb) * 100,
                description=f"User transferring {transferred_mb}MB (5x+ normal session size)",
                expected_behavior=f"Max session normally: {profile.max_data_transfer_session_mb}MB",
                observed_behavior=f"Transferred: {transferred_mb}MB",
                risk_indicators=[
                    "🚨 Classic data exfiltration pattern",
                    "Possible: database dump, customer data theft, IP theft",
                    "Urgency: HIGH - stop immediately if confirmed"
                ],
                timestamp=datetime.utcnow()
            )
        
        return None
    
    def _check_location_anomaly(
        self,
        user_id: str,
        event: Dict,
        profile: UserBehaviorProfile
    ) -> Optional[BehavioralAnomaly]:
        """
        Is user accessing from unusual geography?
        
        Example: User in NYC, 10 minutes later accessing from Shanghai = account takeover
        """
        
        current_location = event.get('location', 'Unknown')
        
        if current_location not in profile.typical_access_locations:
            
            # High severity if: country changed
            is_country_change = self._is_country_change(
                current_location,
                profile.typical_access_locations[0] if profile.typical_access_locations else 'Unknown'
            )
            
            severity = 85 if is_country_change else 40
            
            return BehavioralAnomaly(
                user_id=user_id,
                anomaly_type=BehaviorAnomalyType.LOCATION_BASED,
                severity_score=severity,
                deviation_percentage=100,  # Completely different location
                description=f"User accessing from {current_location} (never seen before)",
                expected_behavior=f"Typical locations: {', '.join(profile.typical_access_locations)}",
                observed_behavior=f"Accessing from: {current_location}",
                risk_indicators=[
                    "🚨 Impossible travel: Could not reach location in time",
                    "Possible: Account takeover / unauthorized access",
                    "Verify: Call user to confirm"
                ] if is_country_change else ["Unusual but possible (travel, VPN)"],
                timestamp=datetime.utcnow()
            )
        
        return None
    
    def _check_frequency_anomaly(
        self,
        user_id: str,
        event: Dict,
        profile: UserBehaviorProfile
    ) -> Optional[BehavioralAnomaly]:
        """
        Is user doing actions WAY MORE OFTEN than normal?
        
        Example: User normally logs in 1x/day, now 20x/day = account brute force
        """
        
        # Would need to track frequency in real system
        # This is simplified for demonstration
        
        return None
    
    def _check_pattern_break(
        self,
        user_id: str,
        event: Dict,
        profile: UserBehaviorProfile
    ) -> Optional[BehavioralAnomaly]:
        """
        Is user accessing SYSTEMS/DATA they never normally touch?
        
        Example: Finance analyst accessing production source code = suspicious
        """
        
        accessed_resource = event.get('resource', '')
        accessed_type = event.get('resource_type', '')
        
        # Check if this resource is in user's normal set
        if accessed_type == 'database' and accessed_resource not in profile.typical_databases:
            
            return BehavioralAnomaly(
                user_id=user_id,
                anomaly_type=BehaviorAnomalyType.PATTERN_BREAK,
                severity_score=65,
                deviation_percentage=100,
                description=f"User accessing database they don't normally use",
                expected_behavior=f"Normally accesses: {', '.join(profile.typical_databases)}",
                observed_behavior=f"Accessing: {accessed_resource}",
                risk_indicators=[
                    "Privilege creep: User gaining access to new data",
                    "Possible: Account compromise / insider threat",
                    "Check: Is this access approved?"
                ],
                timestamp=datetime.utcnow()
            )
        
        return None
    
    def _is_country_change(self, location_a: str, location_b: str) -> bool:
        """Simple check: different countries?"""
        # In production: use geolocation DB
        return location_a.split(',')[-1] != location_b.split(',')[-1]
    
    def combine_anomalies_into_risk(
        self,
        anomalies: List[BehavioralAnomaly]
    ) -> Tuple[float, List[str]]:
        """
        Multiple small anomalies = not a big deal
        Multiple different anomalies TOGETHER = HIGH RISK
        
        Example:
        - Off-hours access (40/100) = maybe working late
        - From new location (30/100) = maybe traveling
        - BOTH + large data transfer (80/100) = INSIDER THREAT (combine to 95/100)
        """
        
        if not anomalies:
            return 0.0, []
        
        # Base score from strongest anomaly
        risk_score = max(a.severity_score for a in anomalies)
        
        # AMPLIFY if multiple different types
        if len(set(a.anomaly_type for a in anomalies)) > 1:
            risk_score = min(100, risk_score * 1.5)  # 1.5x amplification
        
        # Get all risk indicators
        all_risks = []
        for a in anomalies:
            all_risks.extend(a.risk_indicators)
        
        return risk_score, all_risks


# ============================================================
# EXAMPLE: User behavior profiles for common roles
# ============================================================

def get_generic_profiles() -> Dict[str, Dict]:
    """
    Common user profiles by role
    (Real system would learn from actual data)
    """
    return {
        "developer": {
            "typical_login_hours": list(range(8, 18)),
            "typical_login_days": ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            "daily_data_volume_mb": 200.0,
            "max_data_transfer_session_mb": 1000.0,
            "typical_databases": ['PostgresMain', 'MongoTest'],
            "typical_locations": ['Office'],
        },
        
        "analyst": {
            "typical_login_hours": list(range(9, 17)),
            "typical_login_days": ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            "daily_data_volume_mb": 500.0,  # More data access
            "max_data_transfer_session_mb": 2000.0,
            "typical_databases": ['DataWarehouse', 'AnalyticsDB'],
            "typical_locations": ['Office'],
        },
        
        "soc_analyst": {
            "typical_login_hours": list(range(6, 22)),  # Shifted hours
            "typical_login_days": ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],  # Any day
            "daily_data_volume_mb": 1000.0,  # High data access
            "max_data_transfer_session_mb": 5000.0,
            "typical_databases": ['EventLog', 'SecurityDB', 'SIEM'],
            "typical_locations": ['Office', 'SOC_Remote'],
        },
        
        "admin": {
            "typical_login_hours": list(range(8, 18)),
            "typical_login_days": ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
            "daily_data_volume_mb": 500.0,
            "max_data_transfer_session_mb": 10000.0,  # Can transfer large backups
            "typical_databases": ['*'],  # Access to everything
            "typical_locations": ['Office'],
            "uses_admin": True,
        }
    }

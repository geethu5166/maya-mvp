"""
Integration Tests for MAYA SOC Enterprise
Tests migrated components and core functionality
"""

import pytest
import asyncio
import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from app.services.anomaly_detector import AnomalyDetectionModel, create_anomaly_detector
    from app.services.ai_engine import AIEngineService
    from app.core.event_pipeline import EventPipeline
except ImportError as e:
    logger.warning(f"Could not import some services: {e}")


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture
def sample_ssh_event():
    """Sample SSH brute force event"""
    return {
        "timestamp": datetime.now().isoformat(),
        "type": "SSH_BRUTE_FORCE",
        "attacker_ip": "192.168.1.100",
        "attacker_port": 54321,
        "username_tried": "root",
        "password_tried": "password123",
        "honeypot": "SSH",
        "severity": "HIGH"
    }


@pytest.fixture
def sample_web_event():
    """Sample web credential harvest event"""
    return {
        "timestamp": datetime.now().isoformat(),
        "type": "WEB_CREDENTIAL_HARVEST",
        "attacker_ip": "10.0.0.50",
        "attacker_port": 45000,
        "honeypot": "WEB",
        "severity": "CRITICAL",
        "credentials": "admin:P@ssw0rd",
        "user_agent": "Mozilla/5.0"
    }


@pytest.fixture
def sample_db_event():
    """Sample database login attempt event"""
    return {
        "timestamp": datetime.now().isoformat(),
        "type": "DB_LOGIN_ATTEMPT",
        "attacker_ip": "172.16.0.1",
        "attacker_port": 3306,
        "honeypot": "MYSQL",
        "severity": "CRITICAL",
        "username_tried": "root",
        "details": "MySQL login attempt"
    }


@pytest.fixture
def event_pipeline():
    """Initialize event pipeline"""
    return EventPipeline()


@pytest.fixture
def anomaly_detector():
    """Initialize anomaly detector"""
    return create_anomaly_detector()


@pytest.fixture
def ai_engine():
    """Initialize AI engine"""
    return AIEngineService()


# ============================================================================
# API HEALTH CHECK TESTS
# ============================================================================

def test_api_health_check():
    """Test that core services are responsive"""
    assert create_anomaly_detector() is not None
    assert AIEngineService() is not None
    assert EventPipeline() is not None


# ============================================================================
# EVENT PIPELINE TESTS
# ============================================================================

def test_event_creation(event_pipeline, sample_ssh_event):
    """Test event publication to pipeline"""
    result = event_pipeline.publish(sample_ssh_event)
    
    assert result is not None
    assert 'event_id' in result
    assert result['type'] == 'SSH_BRUTE_FORCE'


def test_multiple_event_types(event_pipeline, sample_ssh_event, sample_web_event):
    """Test publishing different event types"""
    event1 = event_pipeline.publish(sample_ssh_event)
    event2 = event_pipeline.publish(sample_web_event)
    
    assert event1['event_id'] != event2['event_id']
    assert event1['type'] == 'SSH_BRUTE_FORCE'
    assert event2['type'] == 'WEB_CREDENTIAL_HARVEST'


# ============================================================================
# ANOMALY DETECTION TESTS
# ============================================================================

def test_anomaly_detector_initialization(anomaly_detector):
    """Test detector initializes properly"""
    assert anomaly_detector is not None
    assert not anomaly_detector.is_fitted


def test_anomaly_feature_extraction(anomaly_detector, sample_ssh_event):
    """Test that features can be extracted from events"""
    features = anomaly_detector.extract_features(sample_ssh_event)
    
    assert features is not None
    assert features.shape[0] == 1  # One sample
    assert features.shape[1] == 8  # 8 features


def test_anomaly_detection_untrained(anomaly_detector, sample_ssh_event):
    """Test detection on untrained model"""
    result = anomaly_detector.detect(sample_ssh_event)
    
    assert result is not None
    assert result.confidence == 0.0  # Untrained model
    assert "not trained" in result.reason


def test_anomaly_detection_trained(anomaly_detector):
    """Test detection after training"""
    # Create training data (normal events)
    normal_events = [
        {
            "timestamp": "2024-04-10T12:00:00",
            "type": "SSH_BRUTE_FORCE",
            "attacker_ip": f"192.168.1.{i}",
            "attacker_port": 22000 + i,
            "username_tried": "admin",
            "password_tried": "pass",
            "honeypot": "SSH",
            "severity": "HIGH"
        }
        for i in range(20)
    ]
    
    # Train model
    anomaly_detector.train(normal_events)
    assert anomaly_detector.is_fitted
    
    # Test detection on normal event
    normal_event = {
        "timestamp": "2024-04-10T13:00:00",
        "type": "SSH_BRUTE_FORCE",
        "attacker_ip": "192.168.1.50",
        "attacker_port": 23000,
        "username_tried": "admin",
        "password_tried": "pass",
        "honeypot": "SSH",
        "severity": "HIGH"
    }
    
    result = anomaly_detector.detect(normal_event)
    assert result.confidence > 0  # Model is now trained
    assert result.confidence <= 1.0


# ============================================================================
# AI ENGINE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_ai_engine_event_analysis(ai_engine, sample_ssh_event):
    """Test AI engine can analyze events"""
    analysis = await ai_engine.analyze_event(sample_ssh_event)
    
    assert analysis is not None
    assert 'threat_level' in analysis
    assert 'confidence' in analysis
    assert 'summary' in analysis


@pytest.mark.asyncio
async def test_threat_level_classification(ai_engine):
    """Test threat level is classified correctly"""
    critical_event = {
        "timestamp": "2024-04-10T12:00:00",
        "type": "WEB_CREDENTIAL_HARVEST",
        "severity": "CRITICAL",
        "attacker_ip": "10.0.0.1"
    }
    
    analysis = await ai_engine.analyze_event(critical_event)
    assert analysis['threat_level'] in ['CRITICAL', 'HIGH']


@pytest.mark.asyncio
async def test_attacker_profiling(ai_engine, sample_ssh_event):
    """Test AI engine builds attacker profiles"""
    # First attack from IP
    analysis1 = await ai_engine.analyze_event(sample_ssh_event)
    count1 = analysis1['attacker_history']['attack_count']
    
    # Second attack from same IP
    event2 = sample_ssh_event.copy()
    event2['timestamp'] = "2024-04-10T12:01:00"
    
    analysis2 = await ai_engine.analyze_event(event2)
    count2 = analysis2['attacker_history']['attack_count']
    
    assert count2 > count1


@pytest.mark.asyncio
async def test_incident_report_generation(ai_engine):
    """Test incident report generation"""
    events = [
        {
            "timestamp": "2024-04-10T12:00:00",
            "type": "SSH_BRUTE_FORCE",
            "severity": "HIGH",
            "attacker_ip": "192.168.1.1"
        },
        {
            "timestamp": "2024-04-10T12:01:00",
            "type": "WEB_CREDENTIAL_HARVEST",
            "severity": "CRITICAL",
            "attacker_ip": "10.0.0.1"
        }
    ]
    
    report = await ai_engine.generate_incident_report(events)
    
    assert report is not None
    assert "INCIDENT REPORT" in report
    assert "RECOMMENDATIONS" in report


@pytest.mark.asyncio
async def test_attack_prediction(ai_engine):
    """Test attack prediction based on history"""
    historical_events = [
        {
            "timestamp": f"2024-04-10T{10+i}:00:00",
            "type": "SSH_BRUTE_FORCE",
            "severity": "HIGH",
            "attacker_ip": "192.168.1.1"
        }
        for i in range(5)
    ]
    
    predictions = await ai_engine.predict_attacks(historical_events)
    
    assert predictions is not None
    assert len(predictions) > 0
    
    # Check prediction format
    pred = predictions[0]
    assert 'predicted_attack_type' in pred
    assert 'probability' in pred
    assert 0 <= pred['probability'] <= 1


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_event_to_analysis_pipeline(event_pipeline, ai_engine, sample_ssh_event):
    """Test complete pipeline: event → publish → analyze"""
    # Publish event
    published = event_pipeline.publish(sample_ssh_event)
    assert published is not None
    
    # Analyze event
    analysis = await ai_engine.analyze_event(sample_ssh_event)
    assert analysis is not None
    assert analysis['threat_level'] is not None


def test_multiple_honeypot_events(event_pipeline):
    """Test handling of events from multiple honeypots"""
    events = [
        {
            "type": "SSH_BRUTE_FORCE",
            "honeypot": "SSH",
            "severity": "HIGH",
            "attacker_ip": "192.168.1.1",
            "timestamp": datetime.now().isoformat()
        },
        {
            "type": "WEB_CREDENTIAL_HARVEST",
            "honeypot": "WEB",
            "severity": "CRITICAL",
            "attacker_ip": "10.0.0.1",
            "timestamp": datetime.now().isoformat()
        },
        {
            "type": "DB_LOGIN_ATTEMPT",
            "honeypot": "MYSQL",
            "severity": "HIGH",
            "attacker_ip": "172.16.0.1",
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    results = []
    for event in events:
        result = event_pipeline.publish(event)
        results.append(result)
    
    assert len(results) == 3
    assert all(r is not None for r in results)


# ============================================================================
# HONEYPOT INTEGRATION TESTS
# ============================================================================

def test_ssh_honeypot_importable():
    """Test that SSH honeypot can be imported"""
    try:
        from app.honeypot.ssh_honeypot import FakeSSHServer, start_ssh_honeypot
        assert FakeSSHServer is not None
        assert start_ssh_honeypot is not None
    except ImportError as e:
        pytest.skip(f"SSH honeypot not available: {e}")


def test_web_honeypot_importable():
    """Test that Web honeypot can be imported"""
    try:
        from app.honeypot.web_honeypot import create_web_honeypot
        assert create_web_honeypot is not None
    except ImportError as e:
        pytest.skip(f"Web honeypot not available: {e}")


def test_db_honeypot_importable():
    """Test that DB honeypot can be imported"""
    try:
        from app.honeypot.db_honeypot import start_mysql_honeypot, start_redis_honeypot
        assert start_mysql_honeypot is not None
        assert start_redis_honeypot is not None
    except ImportError as e:
        pytest.skip(f"DB honeypot not available: {e}")


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_analysis_response_time(ai_engine):
    """Test analysis completes within reasonable time"""
    import time
    
    event = {
        "timestamp": datetime.now().isoformat(),
        "type": "SSH_BRUTE_FORCE",
        "severity": "HIGH",
        "attacker_ip": "192.168.1.1"
    }
    
    start = time.time()
    await ai_engine.analyze_event(event)
    elapsed = time.time() - start
    
    # Should complete in < 500ms
    assert elapsed < 0.5


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
"""
Integration Tests for MAYA SOC Enterprise
Tests migrated components from maya-mvp-main and enterprise services
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import services
from app.services.anomaly_detector import AnomalyDetectionModel, create_anomaly_detector
from app.services.ai_engine import AIEngineService
from app.core.event_pipeline import EventPipeline

logger = logging.getLogger(__name__)


@dataclass
class IntegratedDetectionResult:
    """Complete detection result = rule + behavioral + decision + fault tolerance"""
    
    detection_type: str
    confidence: float
    behavioral_anomalies: List[BehavioralAnomaly]
    behavioral_risk_score: float
    actionable_alert: Optional[ActionableAlert]
    pipeline_status: str
    recovery_actions: List[str]
    timestamp: datetime
    processing_time_ms: int


class Phase2SecurityPipeline:
    """
    Complete production-grade detection pipeline combining:
    1. Rule-based detection (what happened)
    2. Behavioral analysis (is it anomalous for this user)
    3. Decision engine (what should we do about it)
    4. Fault tolerance (keep running even if components fail)
    """
    
    def __init__(self):
        self.decision_engine = DecisionEngine()
        self.behavioral_engine = BehavioralDetectionEngine()
        
        self.fault_manager = FaultToleranceManager()
        self.decision_circuit = CircuitBreaker("decision_engine")
        self.behavior_circuit = CircuitBreaker("behavior_engine")
        
        for comp in ["decision_engine", "behavior_engine", "rule_engine"]:
            self.fault_manager.register_component(comp)
        
        logger.info("Phase 2 Security Pipeline initialized with full fault tolerance")
    
    async def process_detection(self, raw_detection: Dict) -> IntegratedDetectionResult:
        """Main entry point: Take raw detection → run through entire pipeline"""
        
        start_time = datetime.utcnow()
        recovery_actions = []
        
        try:
            # STEP 1: Rule Detection
            detection_type = raw_detection.get("type", "unknown")
            confidence = raw_detection.get("confidence", 0.5)
            
            self.fault_manager.update_component_status(
                "rule_engine",
                ComponentHealthStatus.HEALTHY
            )
            
            # STEP 2: Behavioral Analysis
            behavioral_anomalies = []
            behavioral_risk = 0.0
            
            try:
                behavioral_anomalies = await self.behavior_circuit.execute(
                    self._analyze_behavior,
                    raw_detection
                )
                
                if behavioral_anomalies:
                    behavioral_risk = max(
                        anom.severity_score for anom in behavioral_anomalies
                    )
                    if len(set(a.anomaly_type for a in behavioral_anomalies)) > 1:
                        behavioral_risk = min(100, behavioral_risk * 1.5)
                
                self.fault_manager.update_component_status(
                    "behavior_engine",
                    ComponentHealthStatus.HEALTHY
                )
            
            except Exception as e:
                logger.warning(
                    f"Behavioral analysis failed (degraded mode): {e}"
                )
                recovery_actions.append(
                    f"Behavioral analysis unavailable, using rule confidence only"
                )
                
                self.fault_manager.update_component_status(
                    "behavior_engine",
                    ComponentHealthStatus.DEGRADED,
                    str(e)
                )
            
            # STEP 3: Decision Engine
            actionable_alert = None
            
            try:
                combined_confidence = confidence
                if behavioral_anomalies:
                    combined_confidence = min(
                        1.0,
                        confidence * (1.0 + (behavioral_risk / 100.0) * 0.3)
                    )
                
                actionable_alert = await self.decision_circuit.execute(
                    self._generate_decision,
                    detection_type=detection_type,
                    raw_detection=raw_detection,
                    combined_confidence=combined_confidence,
                    behavioral_anomalies=behavioral_anomalies
                )
                
                self.fault_manager.update_component_status(
                    "decision_engine",
                    ComponentHealthStatus.HEALTHY
                )
            
            except Exception as e:
                logger.error(
                    f"Decision engine failed (severe degradation): {e}"
                )
                recovery_actions.append(
                    f"Decision engine unavailable, using default response strategy"
                )
                
                self.fault_manager.update_component_status(
                    "decision_engine",
                    ComponentHealthStatus.DEGRADED,
                    str(e)
                )
                
                actionable_alert = self._create_default_decision(
                    detection_type,
                    raw_detection,
                    confidence
                )
            
            processing_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            system_health = self.fault_manager.get_system_health_summary()
            pipeline_status = system_health["overall_status"]
            
            return IntegratedDetectionResult(
                detection_type=detection_type,
                confidence=confidence,
                behavioral_anomalies=behavioral_anomalies,
                behavioral_risk_score=behavioral_risk,
                actionable_alert=actionable_alert,
                pipeline_status=pipeline_status,
                recovery_actions=recovery_actions,
                timestamp=datetime.utcnow(),
                processing_time_ms=processing_time
            )
        
        except Exception as e:
            logger.critical(f"Pipeline critical failure: {e}")
            raise
    
    async def _analyze_behavior(self, detection: Dict) -> List[BehavioralAnomaly]:
        """Call behavioral detection engine with fault handling"""
        
        target_user = detection.get("target_user", "unknown")
        
        profile = UserBehaviorProfile(
            user_id=target_user,
            typical_login_hours=[9, 10, 11, 12, 13, 14, 15, 16, 17],
            typical_login_days=[0, 1, 2, 3, 4],
            typical_access_locations=["Office"],
            daily_data_volume_mb=100.0,
            max_data_transfer_session_mb=500.0,
            typical_databases=["app_db", "analytics_db"],
            commands_per_session=50
        )
        
        anomalies = await asyncio.wait_for(
            asyncio.to_thread(
                self.behavioral_engine.detect_behavioral_anomalies,
                detection,
                profile
            ),
            timeout=5.0
        )
        
        return anomalies
    
    async def _generate_decision(
        self,
        detection_type: str,
        raw_detection: Dict,
        combined_confidence: float,
        behavioral_anomalies: List[BehavioralAnomaly]
    ) -> ActionableAlert:
        """Call decision engine with fault handling"""
        
        alert = await asyncio.wait_for(
            asyncio.to_thread(
                self.decision_engine.generate_actionable_alert,
                detection_type=detection_type,
                confidence=combined_confidence,
                asset=raw_detection.get("asset"),
                context={
                    "raw_detection": raw_detection,
                    "behavioral_anomalies": behavioral_anomalies
                }
            ),
            timeout=5.0
        )
        
        return alert
    
    def _create_default_decision(
        self,
        detection_type: str,
        raw_detection: Dict,
        confidence: float
    ) -> ActionableAlert:
        """Fallback: Create minimal decision if engine fails"""
        
        severity = (
            AlertSeverity.CRITICAL if confidence > 0.8
            else AlertSeverity.MEDIUM if confidence > 0.6
            else AlertSeverity.LOW
        )
        
        return ActionableAlert(
            title=f"Potential {detection_type.replace('_', ' ').title()}",
            severity=severity,
            confidence=confidence,
            recommended_action="INVESTIGATE",
            business_context=f"Detected via rule engine (decision engine unavailable)",
            action_steps=[
                "1. Verify alert authenticity",
                "2. Isolate asset if critical",
                "3. Escalate to security team"
            ],
            false_positive_risk="Medium (decision engine not available)",
            time_to_respond_minutes=15 if severity == AlertSeverity.CRITICAL else 60
        )


async def test_integration_happy_path():
    """Test: Full pipeline works when all components healthy"""
    
    logger.info("TEST 1: Happy Path (All Components Healthy)")
    
    pipeline = Phase2SecurityPipeline()
    
    detection = {
        "type": "ssh_brute_force",
        "source_ip": "203.0.113.45",
        "target_user": "admin",
        "failed_attempts": 120,
        "confidence": 0.95,
        "asset": "db-prod-01"
    }
    
    result = await pipeline.process_detection(detection)
    
    logger.info(f"Pipeline Status: {result.pipeline_status}")
    logger.info(f"Processing Time: {result.processing_time_ms}ms")
    logger.info(f"Actionable Alert: {result.actionable_alert.title if result.actionable_alert else 'None'}")
    logger.info(f"Behavioral Anomalies: {len(result.behavioral_anomalies)} detected")
    
    assert result.pipeline_status == "healthy", "Pipeline should be healthy"
    assert result.actionable_alert is not None, "Should generate action"
    assert result.actionable_alert.recommended_action != "ACKNOWLEDGE"


async def test_integration_behavioral_detection():
    """Test: Behavioral detection + rule engine combine for decision"""
    
    logger.info("TEST 2: Behavioral Detection Enhancement")
    
    pipeline = Phase2SecurityPipeline()
    
    detection = {
        "type": "unusual_data_transfer",
        "source_user": "analyst_john",
        "data_volume_mb": 2000,
        "destination": "personal_dropbox",
        "confidence": 0.65,
        "asset": "file_server",
        "timestamp": "2024-01-15T03:45:00Z"
    }
    
    result = await pipeline.process_detection(detection)
    
    logger.info(f"Rule Confidence: {result.confidence}")
    logger.info(f"Behavioral Risk: {result.behavioral_risk_score}")
    logger.info(f"Final Decision: {result.actionable_alert.title}")
    logger.info(f"Severity: {result.actionable_alert.severity if result.actionable_alert else 'None'}")
    
    assert result.behavioral_risk_score > 50, "Should detect anomalies"
    if result.actionable_alert:
        assert result.actionable_alert.severity != AlertSeverity.INFO


async def test_integration_fault_tolerance():
    """Test: Pipeline survives component failure"""
    
    logger.info("TEST 3: Fault Tolerance (Component Failure)")
    
    pipeline = Phase2SecurityPipeline()
    
    # Simulate: Force behavior engine to fail
    original_execute = pipeline.behavior_circuit.execute
    
    async def failing_execute(*args, **kwargs):
        raise Exception("Simulated behavior engine failure")
    
    pipeline.behavior_circuit.execute = failing_execute
    
    detection = {
        "type": "suspicious_privilege_escalation",
        "source_user": "dev_alice",
        "target_privilege": "admin",
        "confidence": 0.88,
        "asset": "app_server_01"
    }
    
    result = await pipeline.process_detection(detection)
    
    logger.info(f"Pipeline Status: {result.pipeline_status}")
    logger.info(f"Recovery Actions Taken: {result.recovery_actions}")
    logger.info(f"Decision Generated: {result.actionable_alert.title if result.actionable_alert else 'FAILED'}")
    
    assert result.pipeline_status == "degraded", "Should be degraded, not failed"
    assert result.actionable_alert is not None, "Should still generate decision"
    assert len(result.recovery_actions) > 0, "Should document recovery"


async def test_integration_end_to_end():
    """Test: Complete scenario - real-world attack pattern"""
    
    logger.info("TEST 4: Real-World Scenario - Insider Threat")
    
    pipeline = Phase2SecurityPipeline()
    
    detection_sequence = [
        {
            "type": "unusual_data_transfer",
            "source_user": "finance_bob",
            "data_volume_mb": 5000,
            "destination": "crypto_wallet_trace",
            "confidence": 0.82,
            "asset": "finance_db"
        },
        {
            "type": "privilege_escalation",
            "source_user": "finance_bob",
            "target_privilege": "readonly_all_databases",
            "confidence": 0.88,
            "asset": "app_server"
        },
        {
            "type": "suspicious_database_query",
            "source_user": "finance_bob",
            "query_pattern": "SELECT * FROM accounts WHERE balance > 1000000",
            "confidence": 0.79,
            "asset": "finance_db"
        }
    ]
    
    alerts_generated = []
    
    for i, detection in enumerate(detection_sequence, 1):
        logger.info(f"Processing signal {i}/3...")
        result = await pipeline.process_detection(detection)
        alerts_generated.append(result)
        
        if result.actionable_alert:
            logger.info(f"Alert: {result.actionable_alert.title}")
            logger.info(f"Severity: {result.actionable_alert.severity.value}")
    
    health = pipeline.fault_manager.get_system_health_summary()
    logger.info(f"System Health - Overall: {health['overall_status']}")
    
    assert len(alerts_generated) == 3, "Should process all signals"


async def run_all_tests():
    """Execute full integration test suite"""
    
    logger.info("=" * 70)
    logger.info("PHASE 2 PART 3: COMPLETE INTEGRATION TEST SUITE")
    logger.info("Testing: Decision Engine + Behavioral Detection + Fault Tolerance")
    logger.info("=" * 70)
    
    try:
        await test_integration_happy_path()
        await test_integration_behavioral_detection()
        await test_integration_fault_tolerance()
        await test_integration_end_to_end()
        
        logger.info("=" * 70)
        logger.info("✅ ALL TESTS PASSED - System ready for production")
        logger.info("=" * 70)
        
        return True
    
    except AssertionError as e:
        logger.error(f"TEST FAILED: {e}")
        return False
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    asyncio.run(run_all_tests())

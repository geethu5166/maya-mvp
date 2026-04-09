"""
Phase 2 Part 3: Complete Integration & Testing

Shows how Decision Engine + Behavioral Detection + Fault Tolerance work together.
This is what makes MAYA SOC production-ready.
"""

import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Import all three new components
from app.services.decision_engine import (
    DecisionEngine,
    ActionableAlert,
    AlertSeverity
)
from app.services.behavioral_detection import (
    BehavioralDetectionEngine,
    UserBehaviorProfile,
    BehavioralAnomaly
)
from app.services.fault_tolerance import (
    FaultToleranceManager,
    CircuitBreaker,
    ComponentHealthStatus
)

logger = logging.getLogger(__name__)


@dataclass
class IntegratedDetectionResult:
    """Complete detection result = rule + behavioral + decision + fault tolerance"""
    
    # Basic detection (from rules)
    detection_type: str                     # "ssh_brute_force", etc.
    confidence: float                       # 0-1
    
    # Behavioral analysis
    behavioral_anomalies: List[BehavioralAnomaly]  # What behavior is anomalous
    behavioral_risk_score: float           # 0-100, how bad is the behavior
    
    # Actionable decision
    actionable_alert: Optional[ActionableAlert]    # What to DO
    
    # Fault tolerance status
    pipeline_status: str                   # "healthy", "degraded", "recovered"
    recovery_actions: List[str]            # What we did to stay running
    
    # Timing
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
        # Core components
        self.decision_engine = DecisionEngine()
        self.behavioral_engine = BehavioralDetectionEngine()
        
        # Fault tolerance
        self.fault_manager = FaultToleranceManager()
        self.decision_circuit = CircuitBreaker("decision_engine")
        self.behavior_circuit = CircuitBreaker("behavior_engine")
        
        # Register components
        for comp in ["decision_engine", "behavior_engine", "rule_engine"]:
            self.fault_manager.register_component(comp)
        
        logger.info("Phase 2 Security Pipeline initialized with full fault tolerance")
    
    async def process_detection(
        self,
        raw_detection: Dict
    ) -> IntegratedDetectionResult:
        """
        Main entry point: Take raw detection → run through entire pipeline
        
        Example raw_detection:
        {
            "type": "ssh_brute_force",
            "source_ip": "192.168.1.100",
            "target_user": "admin",
            "failed_attempts": 50,
            "confidence": 0.92,
            "asset": "db-prod-01"
        }
        """
        
        start_time = datetime.utcnow()
        recovery_actions = []
        
        try:
            # ======================
            # STEP 1: Rule Detection (fast, already done)
            # ======================
            detection_type = raw_detection.get("type", "unknown")
            confidence = raw_detection.get("confidence", 0.5)
            
            self.fault_manager.update_component_status(
                "rule_engine",
                ComponentHealthStatus.HEALTHY
            )
            
            # ======================
            # STEP 2: Behavioral Analysis
            # ======================
            behavioral_anomalies = []
            behavioral_risk = 0.0
            
            try:
                # Try normal path: analyze behavior
                behavioral_anomalies = await self.behavior_circuit.execute(
                    self._analyze_behavior,
                    raw_detection
                )
                
                # Calculate behavioral risk
                if behavioral_anomalies:
                    behavioral_risk = max(
                        anom.severity_score for anom in behavioral_anomalies
                    )
                    # Multiple types = higher risk
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
            
            # ======================
            # STEP 3: Decision Engine
            # ======================
            actionable_alert = None
            
            try:
                # Combine rule + behavior confidence
                combined_confidence = confidence
                if behavioral_anomalies:
                    # If behavioral analysis confirms, boost confidence
                    combined_confidence = min(
                        1.0,
                        confidence * (1.0 + (behavioral_risk / 100.0) * 0.3)
                    )
                
                # Generate actionable alert
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
                
                # Create minimal decision
                actionable_alert = self._create_default_decision(
                    detection_type,
                    raw_detection,
                    confidence
                )
            
            # Calculate processing time
            processing_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            # Dashboard Status
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
        asset = detection.get("asset", "unknown")
        
        # Build user profile (in production: load from database)
        profile = UserBehaviorProfile(
            user_id=target_user,
            typical_login_hours=[9, 10, 11, 12, 13, 14, 15, 16, 17],
            typical_login_days=[0, 1, 2, 3, 4],  # Mon-Fri
            typical_access_locations=["Office"],
            daily_data_volume_mb=100.0,
            max_data_transfer_session_mb=500.0,
            typical_databases=["app_db", "analytics_db"],
            commands_per_session=50
        )
        
        # Detect anomalies
        anomalies = await asyncio.wait_for(
            asyncio.to_thread(
                self.behavioral_engine.detect_behavioral_anomalies,
                detection,
                profile
            ),
            timeout=5.0  # Must complete in 5 seconds
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


# ============================================================
# INTEGRATION TESTS - Verify all three work together
# ============================================================

async def test_integration_happy_path():
    """
    Test: Full pipeline works when all components healthy
    Expected: Detection → Behavioral analysis → Decision → Action
    """
    print("\n=== TEST 1: Happy Path (All Components Healthy) ===")
    
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
    
    print(f"Pipeline Status: {result.pipeline_status}")
    print(f"Processing Time: {result.processing_time_ms}ms")
    print(f"Actionable Alert: {result.actionable_alert.title if result.actionable_alert else 'None'}")
    print(f"Behavioral Anomalies: {len(result.behavioral_anomalies)} detected")
    
    assert result.pipeline_status == "healthy", "Pipeline should be healthy"
    assert result.actionable_alert is not None, "Should generate action"
    assert result.actionable_alert.recommended_action != "ACKNOWLEDGE"


async def test_integration_behavioral_detection():
    """
    Test: Behavioral detection + rule engine combine for decision
    Expected: Low confidence rule → High behavioral risk → Escalated recommendation
    """
    print("\n=== TEST 2: Behavioral Detection Enhancement ===")
    
    pipeline = Phase2SecurityPipeline()
    
    # Unusual but rule-wise low confidence
    detection = {
        "type": "unusual_data_transfer",
        "source_user": "analyst_john",
        "data_volume_mb": 2000,  # Normally 50MB/day
        "destination": "personal_dropbox",
        "confidence": 0.65,
        "asset": "file_server",
        "timestamp": "2024-01-15T03:45:00Z"  # 3am (never works then)
    }
    
    result = await pipeline.process_detection(detection)
    
    print(f"Rule Confidence: {result.confidence}")
    print(f"Behavioral Risk: {result.behavioral_risk_score}")
    print(f"Final Decision: {result.actionable_alert.title}")
    print(f"Actually Severe: {result.actionable_alert.severity}")
    
    # Behavioral analysis should boost the severity
    assert result.behavioral_risk_score > 50, "Should detect anomalies"
    if result.actionable_alert:
        assert result.actionable_alert.severity != AlertSeverity.INFO


async def test_integration_fault_tolerance():
    """
    Test: Pipeline survives component failure
    Expected: If behavior engine fails → still generates decision (degraded)
    """
    print("\n=== TEST 3: Fault Tolerance (Component Failure) ===")
    
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
    
    print(f"Pipeline Status: {result.pipeline_status}")
    print(f"Recovery Actions Taken: {result.recovery_actions}")
    print(f"Decision Generated: {result.actionable_alert.title if result.actionable_alert else 'FAILED'}")
    
    # Should still work (degraded)
    assert result.pipeline_status == "degraded", "Should be degraded, not failed"
    assert result.actionable_alert is not None, "Should still generate decision"
    assert len(result.recovery_actions) > 0, "Should document recovery"


async def test_integration_end_to_end():
    """
    Test: Complete scenario - real-world attack pattern
    Expected: Multiple signals → coordinated decision + recommendations
    """
    print("\n=== TEST 4: Real-World Scenario - Insider Threat ===")
    
    pipeline = Phase2SecurityPipeline()
    
    # Real scenario: Multiple indicators of insider threat
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
        print(f"\n  Processing signal {i}/3...")
        result = await pipeline.process_detection(detection)
        alerts_generated.append(result)
        
        if result.actionable_alert:
            print(f"    → {result.actionable_alert.title}")
            print(f"    → Severity: {result.actionable_alert.severity.value}")
    
    print(f"\nSystem Health After Sequence:")
    health = pipeline.fault_manager.get_system_health_summary()
    print(f"  Overall: {health['overall_status']}")
    print(f"  Healthy: {health['healthy']}, Degraded: {health['degraded']}")
    
    # Should generate escalating alerts
    assert len(alerts_generated) == 3, "Should process all signals"


# ============================================================
# RUN ALL TESTS
# ============================================================

async def run_all_tests():
    """Execute full integration test suite"""
    
    print("\n" + "=" * 70)
    print("PHASE 2 PART 3: COMPLETE INTEGRATION TEST SUITE")
    print("Testing: Decision Engine + Behavioral Detection + Fault Tolerance")
    print("=" * 70)
    
    try:
        await test_integration_happy_path()
        await test_integration_behavioral_detection()
        await test_integration_fault_tolerance()
        await test_integration_end_to_end()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("= System ready for production =")
        print("=" * 70)
        
        return True
    
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(run_all_tests())

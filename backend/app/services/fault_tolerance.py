"""
Fault Tolerance & Error Recovery System

Ensures MAYA SOC keeps running even when components fail.
Not just detection, but RESILIENCE.

Phase 2 Gap Fix: Adds production-grade reliability
"""

from dataclasses import dataclass
from typing import Optional, Callable, Any, Dict, List
from enum import Enum
from datetime import datetime, timedelta
import asyncio
import logging
from functools import wraps
import traceback

logger = logging.getLogger(__name__)


class FailureMode(str, Enum):
    """Types of failures we handle"""
    TIMEOUT = "timeout"                     # Component too slow
    SERVICE_UNAVAILABLE = "unavailable"    # Service down
    DEGRADED = "degraded"                  # Partial failure
    NETWORK_ERROR = "network_error"        # Connection issue
    DATA_ERROR = "data_error"              # Bad data
    UNKNOWN = "unknown"


@dataclass
class RecoveryAction:
    """What to do when failure detected"""
    action_type: str                        # "retry", "fallback", "alert", "isolate"
    max_retries: int = 3
    retry_delay_seconds: int = 5
    timeout_seconds: int = 30
    fallback_behavior: Optional[Callable] = None
    on_permanent_failure: Optional[Callable] = None


class ComponentHealthStatus(Enum):
    """Health of system component"""
    HEALTHY = "healthy"                    # Working normally
    DEGRADED = "degraded"                  # Partially working
    UNHEALTHY = "unhealthy"                # Not working
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Status of one system component"""
    component_name: str
    status: ComponentHealthStatus
    last_check: datetime
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    recovery_attempts: int = 0


class FaultToleranceManager:
    """
    Detects failures + orchestrates recovery
    
    Without this: One component fails → entire system fails
    With this: System degrades gracefully, auto-recovery
    """
    
    def __init__(self):
        self.component_status: Dict[str, ComponentHealth] = {}
        self.failure_history: Dict[str, List[Dict]] = {}
        self.recovery_backoff = {}  # Exponential backoff tracking
    
    def register_component(self, component_name: str) -> None:
        """Track: Component X exists and is important"""
        self.component_status[component_name] = ComponentHealth(
            component_name=component_name,
            status=ComponentHealthStatus.UNKNOWN,
            last_check=datetime.utcnow()
        )
        self.failure_history[component_name] = []
    
    def update_component_status(
        self,
        component_name: str,
        status: ComponentHealthStatus,
        error_message: Optional[str] = None
    ) -> None:
        """Update: Component X is now Y"""
        
        if component_name not in self.component_status:
            self.register_component(component_name)
        
        old_status = self.component_status[component_name].status
        
        self.component_status[component_name] = ComponentHealth(
            component_name=component_name,
            status=status,
            last_check=datetime.utcnow(),
            error_message=error_message,
            consecutive_failures=(
                self.component_status[component_name].consecutive_failures + 1
                if status != ComponentHealthStatus.HEALTHY
                else 0
            ),
            recovery_attempts=self.component_status[component_name].recovery_attempts
        )
        
        # Alert if status change
        if old_status != status:
            logger.warning(
                f"Component {component_name}: {old_status.value} → {status.value} "
                f"({error_message or 'no error'})"
            )
            
            # Log the failure for analysis
            self.failure_history[component_name].append({
                "timestamp": datetime.utcnow(),
                "status": status.value,
                "error": error_message
            })
    
    def with_retry_and_fallback(
        self,
        primary_fn: Callable,
        fallback_fn: Optional[Callable] = None,
        max_retries: int = 3,
        retry_delay_seconds: int = 2,
        timeout_seconds: int = 10,
        component_name: str = "unknown"
    ):
        """
        Decorator: Try primary → if fails, retry → if still fails, use fallback
        
        Usage:
        @fault_manager.with_retry_and_fallback(
            primary_fn=call_kafka,
            fallback_fn=use_redis,
            max_retries=3
        )
        """
        
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                self.register_component(component_name)
                
                last_error = None
                
                # Try primary function
                for attempt in range(max_retries):
                    try:
                        logger.info(
                            f"[{component_name}] Attempt {attempt+1}/{max_retries}"
                        )
                        
                        # Execute with timeout
                        result = await asyncio.wait_for(
                            primary_fn(*args, **kwargs),
                            timeout=timeout_seconds
                        )
                        
                        # Success! Update status
                        self.update_component_status(
                            component_name,
                            ComponentHealthStatus.HEALTHY
                        )
                        
                        return result
                    
                    except asyncio.TimeoutError as e:
                        last_error = e
                        logger.warning(
                            f"[{component_name}] Timeout on attempt {attempt+1}: {e}"
                        )
                        self.update_component_status(
                            component_name,
                            ComponentHealthStatus.DEGRADED,
                            f"Timeout: {str(e)}"
                        )
                    
                    except Exception as e:
                        last_error = e
                        logger.warning(
                            f"[{component_name}] Error on attempt {attempt+1}: {e}"
                        )
                        self.update_component_status(
                            component_name,
                            ComponentHealthStatus.DEGRADED,
                            f"Error: {str(e)}"
                        )
                    
                    # Wait before retry (exponential backoff)
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay_seconds * (2 ** attempt))
                
                # All retries exhausted
                logger.error(
                    f"[{component_name}] All {max_retries} attempts failed. "
                    f"Using fallback strategy."
                )
                
                self.update_component_status(
                    component_name,
                    ComponentHealthStatus.UNHEALTHY,
                    f"Failed after {max_retries} attempts: {str(last_error)}"
                )
                
                # Try fallback if provided
                if fallback_fn:
                    try:
                        logger.info(
                            f"[{component_name}] Activating fallback strategy"
                        )
                        result = await fallback_fn(*args, **kwargs)
                        
                        self.update_component_status(
                            component_name,
                            ComponentHealthStatus.DEGRADED,
                            "Running on fallback (primary unavailable)"
                        )
                        
                        return result
                    
                    except Exception as fb_error:
                        logger.critical(
                            f"[{component_name}] Fallback also failed: {fb_error}"
                        )
                        self.update_component_status(
                            component_name,
                            ComponentHealthStatus.UNHEALTHY,
                            f"Fallback failed: {str(fb_error)}"
                        )
                        raise
                
                else:
                    # No fallback = must fail
                    raise Exception(
                        f"{component_name} permanently failed: {str(last_error)}"
                    )
            
            return wrapper
        
        return decorator
    
    def get_system_health_summary(self) -> Dict:
        """
        Dashboard shows: System health at a glance
        
        Example:
        {
            "overall_status": "degraded",  # Some components down
            "healthy_components": 8,
            "degraded_components": 1,       # Kafka down, using fallback
            "unhealthy_components": 0,
            "components": {...}
        }
        """
        
        statuses = [comp.status for comp in self.component_status.values()]
        
        return {
            "overall_status": self._aggregate_status(statuses),
            "healthy": sum(1 for s in statuses if s == ComponentHealthStatus.HEALTHY),
            "degraded": sum(1 for s in statuses if s == ComponentHealthStatus.DEGRADED),
            "unhealthy": sum(1 for s in statuses if s == ComponentHealthStatus.UNHEALTHY),
            "components": {
                name: {
                    "status": health.status.value,
                    "last_check": health.last_check.isoformat(),
                    "error": health.error_message,
                    "failures": health.consecutive_failures,
                    "recovery_attempts": health.recovery_attempts
                }
                for name, health in self.component_status.items()
            }
        }
    
    def _aggregate_status(self, statuses: List[ComponentHealthStatus]) -> str:
        """Overall system health based on component statuses"""
        
        if any(s == ComponentHealthStatus.UNHEALTHY for s in statuses):
            return "unhealthy"  # Critical component down
        
        if any(s == ComponentHealthStatus.DEGRADED for s in statuses):
            return "degraded"   # Some components down, fallbacks active
        
        if all(s == ComponentHealthStatus.HEALTHY for s in statuses):
            return "healthy"    # Everything working
        
        return "unknown"
    
    def should_alert_on_failure(
        self,
        component_name: str
    ) -> bool:
        """
        Should we ALERT HUMANS about this failure?
        Not every error needs alerting (transient failures don't)
        """
        
        health = self.component_status.get(component_name)
        if not health:
            return False
        
        # Alert if:
        # 1. Component is unhealthy (not just degraded)
        # 2. OR multiple consecutive failures
        # 3. OR critical component down
        
        critical_components = ["kafka", "database", "detection_engine"]
        
        is_critical = component_name in critical_components
        is_unhealthy = health.status == ComponentHealthStatus.UNHEALTHY
        has_multiple_failures = health.consecutive_failures > 3
        
        return is_critical and (is_unhealthy or has_multiple_failures)


class CircuitBreaker:
    """
    Prevent cascading failures:
    
    Without: Component A fails → keeps trying → system slow
    With: Component A fails → STOP trying → fast fail, use fallback
    
    States:
    - CLOSED: Normal operation
    - OPEN: Too many failures, don't even try
    - HALF_OPEN: Testing if recovered yet
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        
        self.state = "closed"  # "closed", "open", "half_open"
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
    
    async def execute(
        self,
        fn: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function through circuit breaker logic"""
        
        # Check if should attempt call
        if self.state == "open":
            # Are we in recovery timeout window?
            if datetime.utcnow() - self.last_failure_time > timedelta(
                seconds=self.recovery_timeout_seconds
            ):
                # Try to recover
                self.state = "half_open"
                logger.info(f"[{self.name}] Circuit breaker entering HALF_OPEN state")
            else:
                # Still in timeout, fail fast
                raise Exception(
                    f"[{self.name}] Circuit breaker is OPEN - fail fast"
                )
        
        # Try to execute
        try:
            result = await fn(*args, **kwargs)
            
            # Success! Reset
            if self.state == "half_open":
                self.state = "closed"
                self.failure_count = 0
                logger.info(f"[{self.name}] Circuit breaker CLOSED (recovered)")
            
            return result
        
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            # Check if should trip circuit
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                logger.error(
                    f"[{self.name}] Circuit breaker OPEN "
                    f"({self.failure_count} failures)"
                )
            
            raise


class PipelineCheckpoint:
    """
    Recovery point in pipeline
    
    If pipeline fails at step 5, restart from last checkpoint (step 3)
    Not from beginning (saves time + resources)
    """
    
    def __init__(self, checkpoint_id: str):
        self.id = checkpoint_id
        self.timestamp = datetime.utcnow()
        self.data: Dict[str, Any] = {}
        self.size_bytes = 0
    
    def save(self, data: Dict[str, Any]) -> None:
        """Save checkpoint to storage"""
        self.timestamp = datetime.utcnow()
        self.data = data
        # In production: save to persistent storage (Redis, DB)
    
    def restore(self) -> Dict[str, Any]:
        """Restore from checkpoint"""
        return self.data


# ============================================================
# EXAMPLE: How to use fault tolerance in event pipeline
# ============================================================

class FaultTolerantEventPipeline:
    """
    Production event pipeline with resilience
    """
    
    def __init__(self):
        self.fault_manager = FaultToleranceManager()
        
        # Register all components
        for component in ["kafka_producer", "kafka_consumer", "database", 
                         "detection_engine", "monitoring"]:
            self.fault_manager.register_component(component)
        
        # Circuit breakers for external calls
        self.kafka_circuit = CircuitBreaker("kafka", failure_threshold=5)
        self.db_circuit = CircuitBreaker("database", failure_threshold=5)
    
    async def process_event_with_recovery(
        self,
        event: Dict
    ) -> Dict:
        """
        Process event with full fault tolerance:
        1. Try Kafka
        2. If fails, try Redis queue
        3. If both fail, store locally + retry later
        """
        
        # Checkpoint: Start of pipeline
        checkpoint = PipelineCheckpoint("event_start")
        checkpoint.save({"event": event, "timestamp": datetime.utcnow()})
        
        try:
            # Step 1: Kafka messaging
            try:
                await self.kafka_circuit.execute(
                    self._send_to_kafka,
                    event
                )
            except Exception as e:
                logger.warning(
                    f"Kafka failed, attempting Redis fallback: {e}"
                )
                # Fallback: Use Redis
                await self._send_to_redis(event)
            
            # Step 2: Detection
            detection_result = await self._run_detection(event)
            
            # Checkpoint: After detection
            checkpoint.save({"detection": detection_result})
            
            # Step 3: Database storage
            try:
                await self.db_circuit.execute(
                    self._store_in_database,
                    event,
                    detection_result
                )
            except Exception as e:
                logger.error(
                    f"Database write failed: {e}. Queuing for retry."
                )
                await self._queue_for_retry(event, detection_result)
            
            # Success
            return {
                "status": "success",
                "event_id": event.get("id"),
                "detection": detection_result
            }
        
        except Exception as e:
            logger.critical(
                f"Event pipeline failed: {e}. Saving checkpoint for recovery."
            )
            # Save checkpoint for recovery
            checkpoint.save({"error": str(e), "event": event})
            raise
    
    async def _send_to_kafka(self, event: Dict) -> None:
        """Send event to Kafka"""
        pass
    
    async def _send_to_redis(self, event: Dict) -> None:
        """Fallback: Send to Redis queue"""
        pass
    
    async def _run_detection(self, event: Dict) -> Dict:
        """Run detection on event"""
        return {"detected": False}
    
    async def _store_in_database(self, event: Dict, detection: Dict) -> None:
        """Store in database"""
        pass
    
    async def _queue_for_retry(self, event: Dict, detection: Dict) -> None:
        """Queue for later retry"""
        pass

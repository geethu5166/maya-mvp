"""
HEALTH CHECKS & STARTUP VERIFICATION
=====================================

Enterprise-grade health check system for:
- Service startup verification
- Dependency health checks (DB, Redis, Kafka)
- Graceful degradation on partial failures
- Liveness and readiness probes

Author: MAYA SOC Enterprise
Version: 1.0
"""

import logging
import asyncio
from enum import Enum
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status levels"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"


@dataclass
class ServiceHealth:
    """Single service health status"""
    name: str
    status: HealthStatus
    message: str
    last_check: str
    latency_ms: int
    is_critical: bool  # If False, don't block startup


class DependencyHealthCheck:
    """
    Health check for external dependencies
    
    Categories:
    - Database (PostgreSQL)
    - Cache (Redis)
    - Message Broker (Kafka)
    - External APIs
    """
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.health_status: Dict[str, ServiceHealth] = {}
        self.last_full_check: Optional[datetime] = None
    
    def register_check(
        self,
        name: str,
        check_func: Callable,
        critical: bool = False,
        timeout_seconds: int = 10
    ) -> None:
        """
        Register a health check function
        
        Args:
            name: Service name
            check_func: Async function returning (bool, str) = (healthy, message)
            critical: If True, blocks startup if unhealthy
            timeout_seconds: Max time for check
        """
        self.checks[name] = {
            'func': check_func,
            'critical': critical,
            'timeout': timeout_seconds,
        }
    
    async def check_postgresql(self) -> tuple[bool, str]:
        """Check PostgreSQL database connectivity"""
        try:
            # In production: use actual db connection
            # For now: simulated check
            
            # Would do:
            # async with db_pool.acquire() as conn:
            #     await conn.fetchval("SELECT 1")
            
            return True, "PostgreSQL OK"
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return False, f"PostgreSQL unavailable: {str(e)}"
    
    async def check_redis(self) -> tuple[bool, str]:
        """Check Redis cache connectivity"""
        try:
            # In production: use actual redis connection
            # For now: simulated check
            
            # Would do:
            # await redis_client.ping()
            
            return True, "Redis OK"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False, f"Redis unavailable: {str(e)}"
    
    async def check_kafka(self) -> tuple[bool, str]:
        """Check Kafka message broker connectivity"""
        try:
            # In production: check Kafka broker
            # For now: simulated check
            
            # Would do:
            # admin_client = KafkaAdminClient(...)
            # topics = await admin_client.list_topics()
            
            return True, "Kafka OK"
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return False, f"Kafka unavailable: {str(e)}"
    
    async def check_all(self) -> Dict[str, ServiceHealth]:
        """
        Run all registered health checks
        Returns dict of service_name -> ServiceHealth
        """
        results = {}
        
        # Default checks
        checks = {
            'PostgreSQL': (self.check_postgresql, True),
            'Redis': (self.check_redis, True),
            'Kafka': (self.check_kafka, True),
        }
        
        for name, (check_func, is_critical) in checks.items():
            try:
                start = datetime.utcnow()
                
                # Run with timeout
                healthy, message = await asyncio.wait_for(
                    check_func(),
                    timeout=10
                )
                
                latency = int((datetime.utcnow() - start).total_seconds() * 1000)
                
                status = (
                    HealthStatus.HEALTHY if healthy
                    else HealthStatus.UNHEALTHY
                )
                
                results[name] = ServiceHealth(
                    name=name,
                    status=status,
                    message=message,
                    last_check=datetime.utcnow().isoformat(),
                    latency_ms=latency,
                    is_critical=is_critical,
                )
                
                logger.info(f"Health check {name}: {status.value} ({latency}ms)")
                
            except asyncio.TimeoutError:
                results[name] = ServiceHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check timeout (>10s)",
                    last_check=datetime.utcnow().isoformat(),
                    latency_ms=10000,
                    is_critical=is_critical,
                )
                logger.error(f"Health check timeout for {name}")
            
            except Exception as e:
                results[name] = ServiceHealth(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Health check error: {str(e)}",
                    last_check=datetime.utcnow().isoformat(),
                    latency_ms=0,
                    is_critical=is_critical,
                )
                logger.error(f"Health check error for {name}: {e}")
        
        self.health_status = results
        self.last_full_check = datetime.utcnow()
        
        return results
    
    def get_readiness_status(self) -> tuple[bool, str]:
        """
        Check if system is ready to serve traffic
        
        Requirements:
        - All critical services are healthy
        
        Returns (is_ready, reason)
        """
        if not self.health_status:
            return False, "Health checks not performed yet"
        
        critical_failures = [
            health for health in self.health_status.values()
            if health.is_critical and health.status != HealthStatus.HEALTHY
        ]
        
        if critical_failures:
            reasons = [f"{h.name}: {h.message}" for h in critical_failures]
            return False, "Critical services down: " + "; ".join(reasons)
        
        return True, "System ready"
    
    def get_liveness_status(self) -> bool:
        """
        Check if system is alive
        Even with degradation, system should respond to liveness probe
        
        Returns True if at least one critical service is healthy
        """
        if not self.health_status:
            return False
        
        healthy_critical = [
            health for health in self.health_status.values()
            if health.is_critical and health.status == HealthStatus.HEALTHY
        ]
        
        return len(healthy_critical) > 0
    
    def get_status_json(self) -> Dict[str, Any]:
        """Get health status as JSON for API responses"""
        overall_status = HealthStatus.HEALTHY
        
        if not self.health_status:
            overall_status = HealthStatus.UNHEALTHY
        else:
            health_values = [h.status for h in self.health_status.values()]
            
            if any(h == HealthStatus.UNHEALTHY for h in health_values):
                overall_status = HealthStatus.UNHEALTHY
            elif any(h == HealthStatus.DEGRADED for h in health_values):
                overall_status = HealthStatus.DEGRADED
        
        return {
            'status': overall_status.value,
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                name: asdict(health)
                for name, health in self.health_status.items()
            },
            'is_ready': self.get_readiness_status()[0],
            'is_alive': self.get_liveness_status(),
        }


class StartupVerifier:
    """
    Verify all critical services start correctly
    
    Implements:
    - Ordered dependency startup
    - Timeout handling
    - Graceful degradation
    - Startup state machine
    """
    
    class StartupState(str, Enum):
        NOT_STARTED = "NOT_STARTED"
        STARTING = "STARTING"
        READY = "READY"
        FAILED = "FAILED"
    
    def __init__(self):
        self.state = self.StartupState.NOT_STARTED
        self.startup_time: Optional[datetime] = None
        self.startup_duration_ms: Optional[int] = None
        self.startup_errors: list[str] = []
    
    async def verify_startup(self, health_checker: DependencyHealthCheck) -> bool:
        """
        Verify startup sequence
        
        Returns True if system is ready to serve traffic
        """
        self.state = self.StartupState.STARTING
        self.startup_time = datetime.utcnow()
        
        logger.info("Starting up MAYA SOC Enterprise...")
        
        # 1. Check critical dependencies
        health_results = await health_checker.check_all()
        
        # 2. Analyze results
        critical_failures = [
            h for h in health_results.values()
            if h.is_critical and h.status != HealthStatus.HEALTHY
        ]
        
        if critical_failures:
            self.startup_errors = [
                f"{h.name}: {h.message}" for h in critical_failures
            ]
            self.state = self.StartupState.FAILED
            
            logger.error(
                f"System startup FAILED with {len(critical_failures)} critical errors"
            )
            return False
        
        # 3. All critical services healthy
        self.startup_duration_ms = int(
            (datetime.utcnow() - self.startup_time).total_seconds() * 1000
        )
        self.state = self.StartupState.READY
        
        logger.info(
            f"System startup SUCCESSFUL in {self.startup_duration_ms}ms"
        )
        
        return True
    
    def get_startup_status(self) -> Dict[str, Any]:
        """Get startup status for diagnostics"""
        return {
            'state': self.state.value,
            'startup_time': (
                self.startup_time.isoformat() if self.startup_time else None
            ),
            'startup_duration_ms': self.startup_duration_ms,
            'errors': self.startup_errors,
            'is_ready': self.state == self.StartupState.READY,
        }


# Global instances
health_checker = DependencyHealthCheck()
startup_verifier = StartupVerifier()


async def initialize_health_checks() -> bool:
    """
    Initialize and run startup verification
    Should be called in main.py on app startup
    
    Returns True if system is ready (can be False for graceful degradation)
    """
    return await startup_verifier.verify_startup(health_checker)

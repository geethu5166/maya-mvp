"""
MAYA SOC Core Module - Enterprise security operations framework
Exports key components for logging, event pipeline, error handling, and service monitoring
"""

# Logging
from app.core.logging_service import (
    setup_logging,
    get_logger,
    JSONFormatter,
    LoggerMixin
)

# Event Pipeline
from app.core.unified_event_pipeline import (
    EventType,
    EventSeverity,
    SecurityEvent,
    EventPublisher,
    KafkaEventPublisher,
    DatabaseEventPublisher,
    UnifiedEventPipeline,
    publish_security_event
)

# Error Handling
from app.core.error_handling import (
    MAYAException,
    ConfigurationError,
    AuthenticationError,
    PipelineError,
    HoneypotError,
    DatabaseError,
    ExternalServiceError,
    safe_async,
    safe_sync,
    retry,
    handle_error,
    log_duration
)

# Service Monitoring
from app.core.watchdog import (
    ServiceStatus,
    ServiceInfo,
    ModuleWatchdog
)

__all__ = [
    # Logging
    "setup_logging",
    "get_logger",
    "JSONFormatter",
    "LoggerMixin",
    
    # Event Pipeline
    "EventType",
    "EventSeverity",
    "SecurityEvent",
    "EventPublisher",
    "KafkaEventPublisher",
    "DatabaseEventPublisher",
    "UnifiedEventPipeline",
    "publish_security_event",
    
    # Error Handling
    "MAYAException",
    "ConfigurationError",
    "AuthenticationError",
    "PipelineError",
    "HoneypotError",
    "DatabaseError",
    "ExternalServiceError",
    "safe_async",
    "safe_sync",
    "retry",
    "handle_error",
    "log_duration",
    
    # Service Monitoring
    "ServiceStatus",
    "ServiceInfo",
    "ModuleWatchdog",
]


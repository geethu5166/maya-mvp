"""
Observability Stack Integration.
Metrics collection, distributed tracing, and monitoring.

Features:
1. Prometheus Metrics (pull-based)
2. Distributed Tracing (OpenTelemetry)
3. Performance Monitoring
4. Health Checks
5. Alert Thresholds
"""

import logging
import time
from typing import Dict, Optional, Any, Callable, List
from datetime import datetime
from functools import wraps
from contextlib import asynccontextmanager

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

logger = logging.getLogger(__name__)


# Global registry
REGISTRY = CollectorRegistry()

# Define metrics
REQUEST_COUNT = Counter(
    'maya_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)

REQUEST_DURATION = Histogram(
    'maya_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
    registry=REGISTRY
)

EVENTS_PROCESSED = Counter(
    'maya_events_processed_total',
    'Total events processed',
    ['event_type', 'severity'],
    registry=REGISTRY
)

EVENTS_INGESTION_RATE = Gauge(
    'maya_event_ingestion_rate',
    'Current event ingestion rate (events/sec)',
    registry=REGISTRY
)

ACTIVE_INCIDENTS = Gauge(
    'maya_active_incidents',
    'Number of active incidents',
    registry=REGISTRY
)

ML_PREDICTION_LATENCY = Histogram(
    'maya_ml_prediction_latency_seconds',
    'ML model prediction latency',
    ['model_name'],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=REGISTRY
)

THREAT_INTEL_CACHE_HIT = Counter(
    'maya_threat_intel_cache_hits_total',
    'Threat intelligence cache hits',
    ['source'],
    registry=REGISTRY
)

THREAT_INTEL_API_CALLS = Counter(
    'maya_threat_intel_api_calls_total',
    'Threat intelligence API calls',
    ['source', 'status'],
    registry=REGISTRY
)

DATABASE_QUERY_DURATION = Histogram(
    'maya_database_query_duration_seconds',
    'Database query duration',
    ['query_type'],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0),
    registry=REGISTRY
)

ERROR_COUNT = Counter(
    'maya_errors_total',
    'Total errors',
    ['error_type', 'component'],
    registry=REGISTRY
)

SERVICE_HEALTH = Gauge(
    'maya_service_health',
    'Service health status (1=healthy, 0=unhealthy)',
    ['service_name'],
    registry=REGISTRY
)


class PerformanceMonitor:
    """Monitor system performance"""
    
    def __init__(self):
        """Initialize performance monitor"""
        self.start_time = time.time()
        self.event_buffer = []
        self.last_event_count = 0
    
    def record_request(self, method: str, endpoint: str, 
                      status_code: int, duration: float) -> None:
        """
        Record HTTP request metrics.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            status_code: Response status code
            duration: Request duration in seconds
        """
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status=status_code
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_event_processing(self, event_type: str, 
                               severity: str) -> None:
        """
        Record event processing.
        
        Args:
            event_type: Type of event
            severity: Severity level
        """
        EVENTS_PROCESSED.labels(
            event_type=event_type,
            severity=severity
        ).inc()
    
    def record_ml_prediction(self, model_name: str, 
                            duration: float) -> None:
        """
        Record ML model prediction.
        
        Args:
            model_name: Name of ML model
            duration: Prediction duration in seconds
        """
        ML_PREDICTION_LATENCY.labels(
            model_name=model_name
        ).observe(duration)
    
    def record_threat_intel_call(self, source: str, 
                                success: bool) -> None:
        """
        Record threat intelligence API call.
        
        Args:
            source: Information source
            success: Whether call was successful
        """
        status = 'success' if success else 'failure'
        THREAT_INTEL_API_CALLS.labels(
            source=source,
            status=status
        ).inc()
    
    def record_cache_hit(self, source: str) -> None:
        """Record cache hit"""
        THREAT_INTEL_CACHE_HIT.labels(source=source).inc()
    
    def record_database_query(self, query_type: str, 
                             duration: float) -> None:
        """
        Record database query.
        
        Args:
            query_type: Type of query
            duration: Query duration in seconds
        """
        DATABASE_QUERY_DURATION.labels(
            query_type=query_type
        ).observe(duration)
    
    def record_error(self, error_type: str, component: str) -> None:
        """
        Record error.
        
        Args:
            error_type: Type of error
            component: Component where error occurred
        """
        ERROR_COUNT.labels(
            error_type=error_type,
            component=component
        ).inc()
    
    def update_service_health(self, service_name: str, 
                             healthy: bool) -> None:
        """
        Update service health status.
        
        Args:
            service_name: Name of service
            healthy: Whether service is healthy
        """
        SERVICE_HEALTH.labels(service_name=service_name).set(
            1 if healthy else 0
        )
    
    def update_active_incidents(self, count: int) -> None:
        """Update active incident count"""
        ACTIVE_INCIDENTS.set(count)
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get current metrics summary.
        
        Returns:
            Dictionary with metrics
        """
        return {
            'uptime_seconds': time.time() - self.start_time,
            'timestamp': datetime.now().isoformat(),
            'total_requests': REQUEST_COUNT._value.get() if hasattr(REQUEST_COUNT, '_value') else 0,
            'total_events_processed': EVENTS_PROCESSED._value.get() if hasattr(EVENTS_PROCESSED, '_value') else 0,
            'active_incidents': ACTIVE_INCIDENTS._value.get() if hasattr(ACTIVE_INCIDENTS, '_value') else 0,
        }


class DistributedTracer:
    """Distributed tracing using OpenTelemetry-like approach"""
    
    def __init__(self):
        """Initialize distributed tracer"""
        self.trace_id_counter = 0
        self.traces: Dict[str, Dict[str, Any]] = {}
    
    def start_trace(self, operation_name: str, 
                   attributes: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new trace.
        
        Args:
            operation_name: Name of operation
            attributes: Optional attributes
            
        Returns:
            Trace ID
        """
        self.trace_id_counter += 1
        trace_id = f"trace_{self.trace_id_counter}"
        
        self.traces[trace_id] = {
            'operation_name': operation_name,
            'start_time': time.time(),
            'attributes': attributes or {},
            'spans': []
        }
        
        return trace_id
    
    def add_span(self, trace_id: str, span_name: str,
                duration: float,
                attributes: Optional[Dict[str, Any]] = None) -> None:
        """
        Add span to trace.
        
        Args:
            trace_id: Trace ID
            span_name: Name of span
            duration: Span duration in seconds
            attributes: Optional attributes
        """
        if trace_id not in self.traces:
            return
        
        span = {
            'name': span_name,
            'duration': duration,
            'timestamp': time.time(),
            'attributes': attributes or {}
        }
        
        self.traces[trace_id]['spans'].append(span)
    
    def end_trace(self, trace_id: str) -> Dict[str, Any]:
        """
        End trace and return trace data.
        
        Args:
            trace_id: Trace ID
            
        Returns:
            Trace data
        """
        if trace_id not in self.traces:
            return {}
        
        trace_data = self.traces[trace_id]
        trace_data['end_time'] = time.time()
        trace_data['total_duration'] = trace_data['end_time'] - trace_data['start_time']
        
        # Keep only recent traces
        if len(self.traces) > 10000:
            oldest_trace_id = min(self.traces.keys(), 
                                 key=lambda k: self.traces[k]['start_time'])
            del self.traces[oldest_trace_id]
        
        return trace_data
    
    async def get_slow_traces(self, threshold: float = 1.0) -> List[Dict[str, Any]]:
        """
        Get traces slower than threshold.
        
        Args:
            threshold: Duration threshold in seconds
            
        Returns:
            List of slow traces
        """
        slow_traces = []
        
        for trace_id, trace_data in self.traces.items():
            if 'total_duration' in trace_data and trace_data['total_duration'] > threshold:
                slow_traces.append(trace_data)
        
        return slow_traces


class HealthCheckService:
    """Health check and readiness probes"""
    
    def __init__(self):
        """Initialize health check service"""
        self.dependencies = {}
    
    def register_dependency(self, name: str, 
                           check_fn: Callable) -> None:
        """
        Register health check for dependency.
        
        Args:
            name: Dependency name
            check_fn: Async function that returns True if healthy
        """
        self.dependencies[name] = check_fn
    
    async def check_health(self) -> Dict[str, Any]:
        """
        Check overall system health.
        
        Returns:
            Health status for all dependencies
        """
        health_status = {}
        all_healthy = True
        
        for name, check_fn in self.dependencies.items():
            try:
                healthy = await check_fn()
                health_status[name] = 'healthy' if healthy else 'unhealthy'
                all_healthy = all_healthy and healthy
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                health_status[name] = 'error'
                all_healthy = False
        
        return {
            'overall_status': 'healthy' if all_healthy else 'unhealthy',
            'components': health_status,
            'timestamp': datetime.now().isoformat()
        }


class ObservabilityStack:
    """Complete observability stack"""
    
    def __init__(self):
        """Initialize observability stack"""
        self.performance_monitor = PerformanceMonitor()
        self.distributed_tracer = DistributedTracer()
        self.health_check = HealthCheckService()
    
    @asynccontextmanager
    async def trace_operation(self, operation_name: str):
        """
        Context manager for tracing operations.
        
        Usage:
            async with observability.trace_operation('process_event'):
                # ... do work ...
        """
        trace_id = self.distributed_tracer.start_trace(operation_name)
        start_time = time.time()
        
        try:
            yield trace_id
        except Exception as e:
            logger.error(f"Operation failed: {e}")
            raise
        finally:
            duration = time.time() - start_time
            self.distributed_tracer.end_trace(trace_id)
    
    def timing_decorator(self, operation_name: str):
        """
        Decorator for timing operations.
        
        Usage:
            @observability.timing_decorator('my_operation')
            async def my_function():
                pass
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time
                    logger.debug(f"{operation_name} took {duration:.4f}s")
            return wrapper
        return decorator


# Global observability instance
observability = ObservabilityStack()

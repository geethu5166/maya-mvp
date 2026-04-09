"""
MONITORING & ALERTING - PROMETHEUS INTEGRATION
================================================

Production monitoring with Prometheus metrics and alerting

Features:
- Event ingestion metrics
- Incident detection metrics
- API performance metrics
- System health metrics
- Prometheus exporter endpoint
- Alert rule definitions

Author: MAYA SOC Enterprise
Version: 1.0
"""

import logging
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Prometheus metric types"""
    COUNTER = "counter"  # Monotonically increasing
    GAUGE = "gauge"  # Can go up or down
    HISTOGRAM = "histogram"  # Distribution
    SUMMARY = "summary"  # Quantiles


@dataclass
class PrometheusMetric:
    """Prometheus metric definition"""
    name: str
    metric_type: MetricType
    description: str
    labels: list = field(default_factory=list)
    value: float = 0.0
    
    def __hash__(self):
        return hash(self.name)


class MetricsRegistry:
    """
    Central metrics registry
    
    Tracks all metrics for Prometheus export
    """
    
    def __init__(self):
        self.metrics: Dict[str, PrometheusMetric] = {}
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, list] = {}
    
    def register_counter(self, name: str, description: str, labels: list = None) -> None:
        """Register a counter metric"""
        metric = PrometheusMetric(
            name=name,
            metric_type=MetricType.COUNTER,
            description=description,
            labels=labels or []
        )
        self.metrics[name] = metric
        self.counters[name] = 0
    
    def register_gauge(self, name: str, description: str, labels: list = None) -> None:
        """Register a gauge metric"""
        metric = PrometheusMetric(
            name=name,
            metric_type=MetricType.GAUGE,
            description=description,
            labels=labels or []
        )
        self.metrics[name] = metric
        self.gauges[name] = 0.0
    
    def register_histogram(self, name: str, description: str, labels: list = None) -> None:
        """Register a histogram metric"""
        metric = PrometheusMetric(
            name=name,
            metric_type=MetricType.HISTOGRAM,
            description=description,
            labels=labels or []
        )
        self.metrics[name] = metric
        self.histograms[name] = []
    
    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment counter"""
        if name in self.counters:
            self.counters[name] += value
    
    def set_gauge(self, name: str, value: float) -> None:
        """Set gauge value"""
        if name in self.gauges:
            self.gauges[name] = value
    
    def add_histogram_sample(self, name: str, value: float) -> None:
        """Add histogram sample"""
        if name in self.histograms:
            self.histograms[name].append(value)
    
    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format
        
        Returns:
            Prometheus-formatted metrics
        """
        
        output = []
        output.append("# HELP maya_soc_metrics MAYA SOC Enterprise Metrics")
        output.append("# TYPE maya_soc_metrics gauge\n")
        
        # Counters
        for name, value in self.counters.items():
            metric = self.metrics.get(name)
            if metric:
                output.append(f"# HELP {name} {metric.description}")
                output.append(f"# TYPE {name} counter")
                output.append(f"{name} {value}")
                output.append("")
        
        # Gauges
        for name, value in self.gauges.items():
            metric = self.metrics.get(name)
            if metric:
                output.append(f"# HELP {name} {metric.description}")
                output.append(f"# TYPE {name} gauge")
                output.append(f"{name} {value}")
                output.append("")
        
        # Histograms
        for name, samples in self.histograms.items():
            metric = self.metrics.get(name)
            if metric and samples:
                output.append(f"# HELP {name} {metric.description}")
                output.append(f"# TYPE {name} histogram")
                
                # Calculate buckets
                sorted_samples = sorted(samples)
                output.append(f"{name}_bucket{{le=\"+Inf\"}} {len(sorted_samples)}")
                output.append(f"{name}_count {len(sorted_samples)}")
                output.append(f"{name}_sum {sum(sorted_samples)}")
                output.append("")
        
        return "\n".join(output)


class MonitoringService:
    """
    Central monitoring service
    
    Tracks:
    - Event pipeline metrics
    - Incident detection metrics
    - API performance
    - System health
    - Database performance
    """
    
    def __init__(self):
        self.registry = MetricsRegistry()
        self._initialize_metrics()
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self._initialize_alert_rules()
    
    def _initialize_metrics(self) -> None:
        """Initialize Prometheus metrics"""
        
        # Event pipeline metrics
        self.registry.register_counter(
            "maya_events_received_total",
            "Total events received"
        )
        self.registry.register_counter(
            "maya_events_processed_total",
            "Total events processed"
        )
        self.registry.register_counter(
            "maya_events_failed_total",
            "Total events that failed processing"
        )
        self.registry.register_gauge(
            "maya_events_queue_size",
            "Current event queue size"
        )
        self.registry.register_histogram(
            "maya_event_processing_latency_ms",
            "Event processing latency in milliseconds"
        )
        
        # Incident metrics
        self.registry.register_counter(
            "maya_incidents_created_total",
            "Total incidents created"
        )
        self.registry.register_gauge(
            "maya_incidents_open",
            "Number of open incidents"
        )
        self.registry.register_gauge(
            "maya_incidents_high_priority",
            "Number of high-priority open incidents"
        )
        self.registry.register_histogram(
            "maya_incident_resolution_time_hours",
            "Incident resolution time in hours"
        )
        
        # Detection metrics
        self.registry.register_counter(
            "maya_detections_triggered_total",
            "Total detections triggered"
        )
        self.registry.register_gauge(
            "maya_detection_rules_active",
            "Number of active detection rules"
        )
        self.registry.register_histogram(
            "maya_detection_confidence_scores",
            "Detection confidence score distribution"
        )
        
        # API metrics
        self.registry.register_counter(
            "maya_api_requests_total",
            "Total API requests"
        )
        self.registry.register_counter(
            "maya_api_errors_total",
            "Total API errors"
        )
        self.registry.register_histogram(
            "maya_api_request_duration_ms",
            "API request duration in milliseconds"
        )
        self.registry.register_gauge(
            "maya_api_requests_in_flight",
            "Current in-flight requests"
        )
        
        # Database metrics
        self.registry.register_gauge(
            "maya_db_connections_open",
            "Currently open database connections"
        )
        self.registry.register_histogram(
            "maya_db_query_duration_ms",
            "Database query duration in milliseconds"
        )
        
        # System metrics
        self.registry.register_gauge(
            "maya_system_cpu_percent",
            "System CPU utilization percentage"
        )
        self.registry.register_gauge(
            "maya_system_memory_percent",
            "System memory utilization percentage"
        )
        self.registry.register_gauge(
            "maya_system_disk_percent",
            "System disk utilization percentage"
        )
        
        logger.info("✓ Prometheus metrics initialized")
    
    def _initialize_alert_rules(self) -> None:
        """Initialize alert rule definitions"""
        
        # Alert 1: High event processing latency
        self.alert_rules['high_event_latency'] = {
            'name': 'HighEventProcessingLatency',
            'description': 'Event processing latency > 1000ms',
            'severity': 'WARNING',
            'metric': 'maya_event_processing_latency_ms',
            'condition': 'avg(maya_event_processing_latency_ms[5m]) > 1000',
            'duration': '5m',
            'actions': ['alert_slack', 'alert_email'],
        }
        
        # Alert 2: High incident backlog
        self.alert_rules['high_incident_backlog'] = {
            'name': 'HighIncidentBacklog',
            'description': 'Open incidents > 50',
            'severity': 'WARNING',
            'metric': 'maya_incidents_open',
            'condition': 'maya_incidents_open > 50',
            'duration': '5m',
            'actions': ['alert_slack'],
        }
        
        # Alert 3: Critical incidents detected
        self.alert_rules['critical_incidents'] = {
            'name': 'CriticalIncidentsDetected',
            'description': 'Critical priority incidents detected',
            'severity': 'CRITICAL',
            'metric': 'maya_incidents_high_priority',
            'condition': 'maya_incidents_high_priority > 5',
            'duration': '1m',
            'actions': ['alert_slack', 'alert_email', 'alert_pagerduty'],
        }
        
        # Alert 4: High API error rate
        self.alert_rules['high_api_error_rate'] = {
            'name': 'HighAPIErrorRate',
            'description': 'API error rate > 5%',
            'severity': 'WARNING',
            'condition': 'rate(maya_api_errors_total[5m]) / rate(maya_api_requests_total[5m]) > 0.05',
            'duration': '10m',
            'actions': ['alert_slack'],
        }
        
        # Alert 5: Database connection pool exhaustion
        self.alert_rules['db_connection_exhaustion'] = {
            'name': 'DBConnectionExhaustion',
            'description': 'Database connections > 18/20 (90%)',
            'severity': 'CRITICAL',
            'metric': 'maya_db_connections_open',
            'condition': 'maya_db_connections_open > 18',
            'duration': '2m',
            'actions': ['alert_slack', 'alert_email'],
        }
        
        logger.info(f"✓ Initialized {len(self.alert_rules)} alert rules")
    
    def record_event_received(self) -> None:
        """Record event received"""
        self.registry.increment_counter("maya_events_received_total", 1)
    
    def record_event_processed(self, latency_ms: int) -> None:
        """Record event processed with latency"""
        self.registry.increment_counter("maya_events_processed_total", 1)
        self.registry.add_histogram_sample("maya_event_processing_latency_ms", latency_ms)
    
    def record_event_failed(self) -> None:
        """Record event processing failure"""
        self.registry.increment_counter("maya_events_failed_total", 1)
    
    def set_event_queue_size(self, size: int) -> None:
        """Update event queue size"""
        self.registry.set_gauge("maya_events_queue_size", size)
    
    def record_incident_created(self) -> None:
        """Record incident creation"""
        self.registry.increment_counter("maya_incidents_created_total", 1)
    
    def set_open_incidents(self, count: int) -> None:
        """Update open incident count"""
        self.registry.set_gauge("maya_incidents_open", count)
    
    def set_high_priority_incidents(self, count: int) -> None:
        """Update high-priority incident count"""
        self.registry.set_gauge("maya_incidents_high_priority", count)
    
    def record_detection_triggered(self, confidence: float) -> None:
        """Record detection with confidence score"""
        self.registry.increment_counter("maya_detections_triggered_total", 1)
        self.registry.add_histogram_sample("maya_detection_confidence_scores", confidence)
    
    def record_api_request(self, latency_ms: int, is_error: bool = False) -> None:
        """Record API request"""
        self.registry.increment_counter("maya_api_requests_total", 1)
        self.registry.add_histogram_sample("maya_api_request_duration_ms", latency_ms)
        
        if is_error:
            self.registry.increment_counter("maya_api_errors_total", 1)
    
    def record_db_query(self, latency_ms: int) -> None:
        """Record database query"""
        self.registry.add_histogram_sample("maya_db_query_duration_ms", latency_ms)
    
    def check_alerts(self) -> list:
        """
        Evaluate alert rules and return triggered alerts
        
        In production: Real Prometheus evaluation
        For now: Simulated alert checking
        
        Returns:
            List of triggered alerts
        """
        
        triggered = []
        
        # Check high event latency
        latency_samples = self.registry.histograms.get("maya_event_processing_latency_ms", [])
        if latency_samples:
            avg_latency = sum(latency_samples) / len(latency_samples)
            if avg_latency > 1000:
                triggered.append({
                    'rule': 'high_event_latency',
                    'message': f'Event latency: {avg_latency:.0f}ms',
                    'severity': 'WARNING',
                })
        
        # Check incident backlog
        open_incidents = self.registry.gauges.get("maya_incidents_open", 0)
        if open_incidents > 50:
            triggered.append({
                'rule': 'high_incident_backlog',
                'message': f'Open incidents: {int(open_incidents)}',
                'severity': 'WARNING',
            })
        
        # Check API error rate
        total_requests = self.registry.counters.get("maya_api_requests_total", 0)
        total_errors = self.registry.counters.get("maya_api_errors_total", 0)
        if total_requests > 0:
            error_rate = total_errors / total_requests
            if error_rate > 0.05:
                triggered.append({
                    'rule': 'high_api_error_rate',
                    'message': f'API error rate: {error_rate*100:.1f}%',
                    'severity': 'WARNING',
                })
        
        return triggered
    
    def export_metrics(self) -> str:
        """Export metrics in Prometheus format"""
        return self.registry.export_prometheus()


# Global monitoring instance
monitoring = MonitoringService()


def track_api_performance(func: Callable) -> Callable:
    """
    Decorator to track API endpoint performance
    
    Usage:
        @app.get("/incidents")
        @track_api_performance
        async def get_incidents():
            ...
    """
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            latency = int((time.time() - start) * 1000)
            monitoring.record_api_request(latency, is_error=False)
            return result
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            monitoring.record_api_request(latency, is_error=True)
            raise
    
    return wrapper


def track_db_performance(func: Callable) -> Callable:
    """
    Decorator to track database query performance
    
    Usage:
        @track_db_performance
        def query_incidents(session):
            ...
    """
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            latency = int((time.time() - start) * 1000)
            monitoring.record_db_query(latency)
            return result
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            monitoring.record_db_query(latency)
            raise
    
    return wrapper

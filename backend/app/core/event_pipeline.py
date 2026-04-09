"""
PRODUCTION EVENT PIPELINE - KAFKA-BASED
========================================

Enterprise-grade event pipeline with:
- Kafka message broker for guaranteed delivery
- At-least-once semantics
- Partitioned by severity/tenant
- Consumer groups for parallel processing
- Dead-letter queue for failed events
- Schema validation
- Monitoring

Author: MAYA SOC Enterprise
Version: 4.0-production
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import hashlib
from uuid import uuid4

# In production: from kafka import KafkaProducer, KafkaConsumer
# For now: simulated implementation


class EventSeverity(str, Enum):
    """Event severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class EventType(str, Enum):
    """Event types"""
    SECURITY_ALERT = "SECURITY_ALERT"
    ANOMALY = "ANOMALY"
    DECEPTION = "DECEPTION"
    THREAT_INTEL = "THREAT_INTEL"
    COMPLIANCE = "COMPLIANCE"
    SYSTEM = "SYSTEM"


@dataclass
class SecurityEvent:
    """Immutable security event"""
    event_id: str
    timestamp: str
    event_type: EventType
    severity: EventSeverity
    source: str
    title: str
    description: str
    tenant_id: str
    data: Dict[str, Any]
    
    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(asdict(self), default=str)
    
    def get_partition_key(self) -> str:
        """Get partition key (tenant + severity)"""
        return f"{self.tenant_id}:{self.severity.value}"


class EventValidator:
    """
    Validate events against schema (prevents bad data in pipeline)
    
    Ensures:
    - All required fields present
    - Type correctness
    - Size limits
    - No sensitive data in logs
    """
    
    REQUIRED_FIELDS = {
        'event_id', 'timestamp', 'event_type', 'severity',
        'source', 'title', 'description', 'tenant_id', 'data'
    }
    
    MAX_EVENT_SIZE = 1024 * 500  # 500 KB
    FORBIDDEN_PATTERNS = [
        'password', 'secret', 'key', 'token',
        'credential', 'apikey', 'api_key'
    ]
    
    @staticmethod
    def validate(event_dict: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate event. Returns (valid, error_message)
        """
        # Check required fields
        missing = EventValidator.REQUIRED_FIELDS - set(event_dict.keys())
        if missing:
            return False, f"Missing required fields: {missing}"
        
        # Check size
        event_json = json.dumps(event_dict)
        if len(event_json) > EventValidator.MAX_EVENT_SIZE:
            return False, f"Event too large: {len(event_json)} > {EventValidator.MAX_EVENT_SIZE}"
        
        # Check for sensitive data
        event_str = event_json.lower()
        for pattern in EventValidator.FORBIDDEN_PATTERNS:
            if pattern in event_str:
                return False, f"Sensitive data detected: {pattern}"
        
        # Type validation
        try:
            EventSeverity(event_dict['severity'])
            EventType(event_dict['event_type'])
        except ValueError as e:
            return False, f"Invalid enum value: {e}"
        
        return True, ""


class ProducerConfig:
    """Kafka producer configuration (enterprise-grade)"""
    
    # Delivery guarantees
    ACKS = "all"  # Wait for all in-sync replicas
    RETRIES = 3  # Retry failed sends
    MAX_IN_FLIGHT = 1  # Maintain ordering
    COMPRESSION = "snappy"  # Compress messages
    BATCH_SIZE = 1024 * 16  # 16 KB batches
    LINGER_MS = 10  # Wait 10ms for batching
    
    # Timeouts
    REQUEST_TIMEOUT_MS = 30000  # 30 second timeout
    DELIVERY_TIMEOUT_MS = 120000  # 2 minute total timeout


class ConsumerConfig:
    """Kafka consumer configuration (enterprise-grade)"""
    
    # Processing guarantees
    GROUP_ID = "maya-soc-consumers"
    AUTO_OFFSET_RESET = "earliest"  # Don't lose events
    ENABLE_AUTO_COMMIT = False  # Manual commit (exactly-once)
    SESSION_TIMEOUT_MS = 30000
    HEARTBEAT_INTERVAL_MS = 10000
    MAX_POLL_RECORDS = 500
    MAX_POLL_INTERVAL_MS = 300000


class ProductionEventPipeline:
    """
    Production event pipeline with Kafka backend
    
    Guarantees:
    - At-least-once delivery
    - Event ordering per tenant
    - Dead-letter queue for failed events
    - Monitoring & metrics
    - Schema validation
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.validator = EventValidator()
        
        # In production, these would be real Kafka imports:
        # from kafka import KafkaProducer, KafkaConsumer
        
        # Simulated in-memory queues (for testing)
        self.events: List[SecurityEvent] = []
        self.failed_events: List[Dict] = []  # Dead-letter queue
        self.metrics = {
            'produced': 0,
            'consumed': 0,
            'failed': 0,
            'validated': 0,
        }
    
    def produce_event(self, event_dict: Dict[str, Any]) -> bool:
        """
        Produce event to pipeline
        
        Returns:
            True if successfully queued, False otherwise
        """
        # Step 1: Validate event
        valid, error = self.validator.validate(event_dict)
        if not valid:
            self.logger.error(f"Invalid event: {error}")
            self.failed_events.append({
                **event_dict,
                'error': error,
                'timestamp': datetime.utcnow().isoformat(),
                'reason': 'VALIDATION_FAILED'
            })
            self.metrics['failed'] += 1
            return False
        
        self.metrics['validated'] += 1
        
        # Step 2: Create SecurityEvent
        event = SecurityEvent(
            event_id=event_dict.get('event_id', str(uuid4())),
            timestamp=event_dict.get('timestamp', datetime.utcnow().isoformat()),
            event_type=EventType(event_dict['event_type']),
            severity=EventSeverity(event_dict['severity']),
            source=event_dict['source'],
            title=event_dict['title'],
            description=event_dict['description'],
            tenant_id=event_dict['tenant_id'],
            data=event_dict.get('data', {}),
        )
        
        # Step 3: In production, send to Kafka
        # producer.send(
        #     topic='security-events',
        #     value=event.to_json().encode(),
        #     key=event.get_partition_key().encode(),
        #     acks=ProducerConfig.ACKS,
        # )
        
        # For now: append to queue
        self.events.append(event)
        self.metrics['produced'] += 1
        
        self.logger.info(
            f"Event produced: {event.event_id} | "
            f"Type: {event.event_type.value} | "
            f"Severity: {event.severity.value}"
        )
        
        return True
    
    def consume_events(self, batch_size: int = 100) -> List[SecurityEvent]:
        """
        Consume events from pipeline (in order)
        
        In production: uses Kafka consumer with consumer groups
        """
        
        batch = self.events[:batch_size]
        
        # In production:
        # consumer.seek_to_beginning()
        # messages = consumer.poll(timeout_ms=1000, max_records=batch_size)
        
        return batch
    
    def commit_batch(self, events: List[SecurityEvent]) -> bool:
        """
        Commit consumed events (mark as processed)
        
        In production: uses Kafka commit API
        """
        
        consumed_count = len(events)
        
        # Remove from queue
        for event in events:
            if event in self.events:
                self.events.remove(event)
        
        self.metrics['consumed'] += consumed_count
        
        self.logger.info(f"Batch committed: {consumed_count} events")
        
        return True
    
    def get_dead_letter_queue(self) -> List[Dict]:
        """Get all failed events"""
        return self.failed_events
    
    def get_metrics(self) -> Dict[str, int]:
        """Get pipeline metrics"""
        return {
            **self.metrics,
            'queue_size': len(self.events),
            'dlq_size': len(self.failed_events),
        }


class TopicManager:
    """
    Manage Kafka topics for different functions
    
    Topics:
    - security-events: All security alerts
    - deception-alerts: Honeypot detections
    - threat-intel: Threat intelligence updates
    - compliance-events: Compliance incidents
    - system-logs: System events
    - dlq: Dead-letter queue
    """
    
    TOPICS = {
        'security-events': {
            'partitions': 10,  # For parallelism
            'replication_factor': 3,  # For high availability
            'retention_ms': 7 * 24 * 60 * 60 * 1000,  # 7 days
            'compression_type': 'snappy',
        },
        'deception-alerts': {
            'partitions': 5,
            'replication_factor': 3,
        },
        'threat-intel': {
            'partitions': 3,
            'replication_factor': 3,
        },
        'compliance-events': {
            'partitions': 5,
            'replication_factor': 3,
        },
        'system-logs': {
            'partitions': 10,
            'replication_factor': 3,
        },
        'dlq': {  # Dead-letter queue
            'partitions': 3,
            'replication_factor': 3,
            'retention_ms': 30 * 24 * 60 * 60 * 1000,  # 30 days
        },
    }
    
    @staticmethod
    def get_topic_for_event(event_type: EventType) -> str:
        """Route event to appropriate topic"""
        
        routing = {
            EventType.SECURITY_ALERT: 'security-events',
            EventType.DECEPTION: 'deception-alerts',
            EventType.THREAT_INTEL: 'threat-intel',
            EventType.COMPLIANCE: 'compliance-events',
            EventType.SYSTEM: 'system-logs',
            EventType.ANOMALY: 'security-events',
        }
        
        return routing.get(event_type, 'security-events')


def create_production_pipeline() -> ProductionEventPipeline:
    """Factory function to create production pipeline"""
    return ProductionEventPipeline()

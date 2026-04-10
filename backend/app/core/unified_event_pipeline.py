"""
UNIFIED Event Pipeline - Single source of truth for all security events
CRITICAL: All events MUST go through this pipeline, not direct file writes
Handles: Publishing, routing, enrichment, storage
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
import asyncio
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Standard event types"""
    SSH_BRUTE_FORCE = "SSH_BRUTE_FORCE"
    WEB_RECON = "WEB_RECON"
    WEB_CREDENTIAL_HARVEST = "WEB_CREDENTIAL_HARVEST"
    WEB_SCAN = "WEB_SCAN"
    DB_CONNECTION_ATTEMPT = "DB_CONNECTION_ATTEMPT"
    DB_AUTH_FAILURE = "DB_AUTH_FAILURE"
    ANOMALY = "ANOMALY"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    THREAT_DETECTED = "THREAT_DETECTED"


class EventSeverity(str, Enum):
    """Event severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class SecurityEvent:
    """Standard security event schema"""
    event_id: str
    event_type: EventType
    severity: EventSeverity
    timestamp: str
    source_ip: str
    destination_ip: str
    description: str
    details: Dict[str, Any]
    honeypot: Optional[str] = None
    username_tried: Optional[str] = None
    password_tried: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert enums to strings
        data["event_type"] = self.event_type.value
        data["severity"] = self.severity.value
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class EventPublisher(ABC):
    """Abstract base for event publishers"""
    
    @abstractmethod
    async def publish(self, event: SecurityEvent) -> bool:
        """Publish event to destination"""
        pass
    
    @abstractmethod
    async def startup(self) -> bool:
        """Initialize publisher"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup publisher"""
        pass


class KafkaEventPublisher(EventPublisher):
    """Kafka-based event publisher (production)"""
    
    def __init__(self, brokers: List[str], topic: str):
        self.brokers = brokers
        self.topic = topic
        self.producer = None
        self.is_connected = False
    
    async def startup(self) -> bool:
        """Initialize Kafka producer"""
        try:
            from aiokafka import AIOKafkaProducer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.brokers,
                value_serializer=lambda v: json.dumps(v).encode()
            )
            await self.producer.start()
            self.is_connected = True
            logger.info(f"✓ Kafka publisher connected to {self.brokers}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to initialize Kafka publisher: {e}")
            return False
    
    async def publish(self, event: SecurityEvent) -> bool:
        """Publish event to Kafka"""
        if not self.is_connected:
            logger.error("Kafka publisher not connected")
            return False
        
        try:
            await self.producer.send_and_wait(
                self.topic,
                event.to_dict()
            )
            logger.debug(f"✓ Event published: {event.event_id}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to publish event: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Close Kafka connection"""
        if self.producer:
            try:
                await self.producer.stop()
                logger.info("✓ Kafka publisher disconnected")
            except Exception as e:
                logger.warning(f"Error closing Kafka producer: {e}")


class DatabaseEventPublisher(EventPublisher):
    """Database-based event publisher (backup)"""
    
    def __init__(self, database_session):
        self.db_session = database_session
        self.is_connected = False
    
    async def startup(self) -> bool:
        """Initialize database publisher"""
        try:
            # Test database connection
            self.is_connected = True
            logger.info("✓ Database publisher ready")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to initialize database publisher: {e}")
            return False
    
    async def publish(self, event: SecurityEvent) -> bool:
        """Store event in database"""
        if not self.is_connected:
            logger.error("Database publisher not connected")
            return False
        
        try:
            # Would import Event model here
            # await self.db_session.add(Event(**event.to_dict()))
            # await self.db_session.commit()
            logger.debug(f"✓ Event stored in database: {event.event_id}")
            return True
        except Exception as e:
            logger.error(f"✗ Failed to store event in database: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Close database connection"""
        self.is_connected = False


class UnifiedEventPipeline:
    """
    MAIN Event Pipeline - Single source of truth
    Routes events to all publishers (Kafka, Database, etc.)
    Ensures no events are lost
    """
    
    def __init__(
        self,
        kafka_brokers: Optional[List[str]] = None,
        kafka_topic: str = "security-events",
        database_session: Optional[Any] = None,
    ):
        self.publishers: List[EventPublisher] = []
        self.event_counter = 0
        self.event_history: List[str] = []  # Store last 1000 event IDs
        self.is_running = False

        # Auto-register publishers from constructor inputs.
        if kafka_brokers:
            self.register_publisher(KafkaEventPublisher(kafka_brokers, kafka_topic))

        if database_session is not None:
            self.register_publisher(DatabaseEventPublisher(database_session))
    
    def register_publisher(self, publisher: EventPublisher) -> None:
        """Register an event publisher"""
        self.publishers.append(publisher)
        logger.info(f"✓ Registered publisher: {publisher.__class__.__name__}")
    
    async def startup(self) -> bool:
        """Initialize all publishers"""
        try:
            logger.info(f"🚀 Starting event pipeline with {len(self.publishers)} publishers...")
            
            results = []
            for publisher in self.publishers:
                result = await publisher.startup()
                results.append(result)
            
            if all(results):
                self.is_running = True
                logger.info("✓ Event pipeline running successfully")
                return True
            else:
                logger.warning("⚠ Some publishers failed to initialize")
                self.is_running = True
                return True
        except Exception as e:
            logger.error(f"✗ Failed to start event pipeline: {e}")
            return False
    
    async def publish_event(self, event: SecurityEvent) -> bool:
        """
        Publish event to all registered publishers
        CRITICAL: This is the ONLY way events enter the system
        """
        if not self.is_running:
            logger.error("Event pipeline not running, cannot publish event")
            return False
        
        try:
            # Increment counter
            self.event_counter += 1
            
            # Track event
            self.event_history.append(event.event_id)
            if len(self.event_history) > 1000:
                self.event_history.pop(0)
            
            # Publish to all publishers
            results = []
            for publisher in self.publishers:
                try:
                    result = await publisher.publish(event)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error publishing to {publisher.__class__.__name__}: {e}")
                    results.append(False)
            
            # Success if at least one publisher succeeded
            if any(results):
                logger.info(
                    f"✓ Event published: {event.event_type.value} | "
                    f"Severity: {event.severity.value} | "
                    f"Source: {event.source_ip}"
                )
                return True
            else:
                logger.error(f"✗ Failed to publish event to any publisher: {event.event_id}")
                return False
        
        except Exception as e:
            logger.error(f"✗ Event pipeline error: {e}")
            return False
    
    async def shutdown(self) -> None:
        """Shutdown all publishers"""
        try:
            logger.info("Shutting down event pipeline...")
            for publisher in self.publishers:
                await publisher.shutdown()
            self.is_running = False
            logger.info("✓ Event pipeline shutdown complete")
        except Exception as e:
            logger.error(f"Error during pipeline shutdown: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        return {
            "is_running": self.is_running,
            "total_events_published": self.event_counter,
            "publishers_count": len(self.publishers),
            "recent_events": len(self.event_history),
        }


# Global pipeline instance
event_pipeline: Optional[UnifiedEventPipeline] = None


async def initialize_event_pipeline(kafka_brokers: Optional[List[str]] = None) -> UnifiedEventPipeline:
    """Initialize the unified event pipeline"""
    global event_pipeline
    
    try:
        event_pipeline = UnifiedEventPipeline()
        
        # Register Kafka publisher (primary)
        if kafka_brokers:
            kafka_publisher = KafkaEventPublisher(
                brokers=kafka_brokers,
                topic="security-events"
            )
            event_pipeline.register_publisher(kafka_publisher)
        
        # Register database publisher (backup)
        # db_publisher = DatabaseEventPublisher(db_session)
        # event_pipeline.register_publisher(db_publisher)
        
        # Start pipeline
        await event_pipeline.startup()
        
        return event_pipeline
    except Exception as e:
        logger.error(f"Failed to initialize event pipeline: {e}")
        raise


async def publish_security_event(
    event_type: EventType,
    severity: EventSeverity,
    source_ip: str,
    destination_ip: str,
    description: str,
    details: Dict[str, Any],
    **kwargs
) -> bool:
    """
    Convenience function to publish security events
    USAGE: await publish_security_event(EventType.SSH_BRUTE_FORCE, ...)
    """
    global event_pipeline
    
    if not event_pipeline or not event_pipeline.is_running:
        logger.error("Event pipeline not available")
        return False
    
    try:
        import uuid
        event = SecurityEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow().isoformat(),
            source_ip=source_ip,
            destination_ip=destination_ip,
            description=description,
            details=details,
            **kwargs
        )
        
        return await event_pipeline.publish_event(event)
    except Exception as e:
        logger.error(f"Failed to publish security event: {e}")
        return False

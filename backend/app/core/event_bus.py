"""Event Bus - Kafka-based event streaming"""

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from aiokafka import AIOKafkaProducer
from .config import get_settings

settings = get_settings()


@dataclass
class SecurityEvent:
    event_id: str
    event_type: str
    severity: str
    source_ip: str
    destination_ip: str
    timestamp: str
    description: str
    metadata: Dict[str, Any]
    module: str
    
    def to_json(self) -> str:
        return json.dumps(asdict(self))


class EventBus:
    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self.running = False
    
    async def connect(self):
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: v.encode() if isinstance(v, str) else v
            )
            await self.producer.start()
            self.running = True
        except Exception as e:
            raise
    
    async def disconnect(self):
        if self.producer:
            await self.producer.stop()
        self.running = False
    
    async def publish_event(self, topic: str, event: SecurityEvent):
        if not self.running:
            return
        try:
            await self.producer.send_and_wait(topic, value=event.to_json(), key=event.source_ip.encode())
        except Exception:
            pass


event_bus = EventBus()


async def get_event_bus() -> EventBus:
    return event_bus

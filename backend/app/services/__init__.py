# Project Structure

- cybersecurity_soc/
  - backend/
    - app/
      - core/
        - cache.py
        - event_bus.py
        - security.py
      - services/
        - ai_engine.py
        - anomaly_detector.py
        - risk_scorer.py
      - main.py
    - requirements.txt
  - frontend/
    - src/
      - components/
        - AlertTable.tsx
        - AIAnalyst.tsx
        - Header.tsx
        - IncidentPanel.tsx
        - RiskScoreCard.tsx
        - StatisticCard.tsx
        - ThreatMap.tsx
        - ThreatTempo.tsx
      - hooks/
        - useAuth.ts
        - useWebSocket.ts
      - pages/
        - Dashboard.tsx
      - utils/
        - classnames.ts
    - package.json

# backend/app/core/cache.py
"""
Distributed caching layer using Redis
Supports: Cache-aside, Write-through, TTL, Pub/Sub
"""

import redis.asyncio as redis
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError
import json
import logging
import pickle
from typing import Any, Optional, Dict, List
from datetime import timedelta, datetime
import hashlib
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

class CacheManager:
    """
    Advanced Redis cache manager with:
    - Connection pooling
    - Automatic serialization
    - TTL management
    - Cache invalidation
    - Stats tracking
    """
    
    def __init__(self, redis_url: str, pool_size: int = 50):
        self.redis_url = redis_url
        self.operations_count = 0
    
    async def connect(self):
        """Initialize Redis connection pool"""
    
    async def disconnect(self):
        """Close Redis connections"""
    
    async def ping(self) -> bool:
        """Health check"""
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
    
    async def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL"""
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
    
    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
    
    async def increment(self, key: str, increment: int = 1) -> int:
        """Increment counter"""
    
    async def decrement(self, key: str, decrement: int = 1) -> int:
        """Decrement counter"""
    
    async def hset(self, name: str, mapping: Dict[str, Any]) -> int:
        """Set hash mapping"""
    
    async def hget(self, name: str, key: str) -> Optional[Any]:
        """Get hash value"""
    
    async def lpush(self, key: str, *values: Any) -> int:
        """Push to list (queue)"""
    
    async def rpop(self, key: str) -> Optional[Any]:
        """Pop from list (queue)"""
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """Get range from list"""
    
    async def _setup_pubsub(self):
        """Setup Redis pub/sub for cache invalidation"""
    
    async def publish_invalidation(self, key: str):
        """Publish cache invalidation event"""
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""

def cached(ttl_seconds: int = 3600, key_prefix: str = "cache"):
    """Decorator to cache async function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Caching logic here
            pass
        return wrapper
    return decorator

# backend/app/core/event_bus.py
"""
Apache Kafka-based event streaming platform
Handles all event ingestion, processing, and distribution
"""

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError
import json
import logging
import asyncio
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime
import time
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    """Standard event types"""
    SSH_BRUTE_FORCE = "SSH_BRUTE_FORCE"
    WEB_SCAN = "WEB_SCAN"
    WEB_CREDENTIAL_HARVEST = "WEB_CREDENTIAL_HARVEST"
    DB_INJECTION = "DB_INJECTION"
    RANSOMWARE_BEHAVIOR = "RANSOMWARE_BEHAVIOR"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"
    LATERAL_MOVEMENT = "LATERAL_MOVEMENT"
    DATA_EXFILTRATION = "DATA_EXFILTRATION"
    MALWARE_EXECUTION = "MALWARE_EXECUTION"
    COMMAND_CONTROL = "COMMAND_CONTROL"
    RECONNAISSANCE = "RECONNAISSANCE"
    EXPLOITATION = "EXPLOITATION"
    PERSISTENCE = "PERSISTENCE"

class Severity(str, Enum):
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
    severity: Severity
    source: str
    timestamp: datetime
    ip_address: str
    country: Optional[str] = None
    port: Optional[int] = None
    protocol: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    user_agent: Optional[str] = None
    username: Optional[str] = None
    password_attempt: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    tags: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps(self.to_dict(), default=str)

class EventBusManager:
    """
    Advanced Kafka-based event bus
    - High-throughput event ingestion
    - Guaranteed delivery
    - Event correlation
    - Consumer groups
    """
    
    def __init__(self, brokers: List[str]):
        self.brokers = brokers
        self.start_time = time.time()
    
    async def start(self):
        """Initialize Kafka producer and consumers"""
    
    async def stop(self):
        """Gracefully shutdown"""
    
    async def publish_event(self, event: SecurityEvent) -> bool:
        """Publish an event to Kafka"""
    
    async def subscribe(self, callback: Callable[[Dict[str, Any]], None]):
        """Subscribe to events"""
    
    async def _consume_messages(self, callback: Callable):
        """Consume messages from topic"""
    
    async def health_check(self) -> bool:
        """Check Kafka connectivity"""
    
    async def _collect_metrics(self):
        """Collect Kafka metrics every minute"""
    
    @staticmethod
    def _serialize(value: Dict[str, Any]) -> bytes:
        """Serialize event to bytes"""
        return json.dumps(value, default=str).encode('utf-8')
    
    @staticmethod
    def _deserialize(value: bytes) -> Dict[str, Any]:
        """Deserialize event from bytes"""
        return json.loads(value.decode('utf-8'))

_event_bus: Optional[EventBusManager] = None

def get_event_bus() -> EventBusManager:
    """Get or create event bus"""
    return _event_bus

async def init_event_bus(brokers: List[str]) -> EventBusManager:
    """Initialize global event bus"""
    global _event_bus
    _event_bus = EventBusManager(brokers)
    await _event_bus.start()
    return _event_bus

# backend/app/core/security.py
"""
Advanced security layer:
- JWT token management
- OAuth2 integration
- MFA (TOTP)
- API key management
- Password hashing
- Rate limiting
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import pyotp
import qrcode
import logging
from io import BytesIO
import base64
from enum import Enum

logger = logging.getLogger(__name__)

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)

class TokenType(str, Enum):
    """Token types"""
    ACCESS = "access"
    REFRESH = "refresh"
    API_KEY = "api_key"
    MFA = "mfa"

class Token(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    mfa_required: bool = False

class SecurityManager:
    """
    Comprehensive security manager
    """
    
    def __init__(self, secret_key: str, refresh_token_expire_days: int = 7):
        self.secret_key = secret_key
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_token(self, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT token"""
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""
    
    def setup_mfa(self, user_id: str) -> Tuple[str, str]:
        """Setup MFA for user"""
    
    def verify_mfa_token(self, secret: str, token: str, window: int = 1) -> bool:
        """Verify MFA token"""
    
    def generate_api_key(self, user_id: str, name: str) -> str:
        """Generate API key"""
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verify API key"""

# backend/app/services/ai_engine.py
"""
Advanced AI/ML engine with:
- GPT-4 integration
- Custom threat analysis models
- Incident report generation
- Attack prediction
"""

import openai
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
from functools import lru_cache
import pickle
import numpy as np

logger = logging.getLogger(__name__)

class AIEngineService:
    """
    Advanced AI engine for threat analysis
    """
    
    def __init__(self, openai_key: str, model_path: str):
        openai.api_key = openai_key
        self.total_inferences = 0
    
    async def initialize(self):
        """Load ML models"""
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def analyze_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security event"""
    
    async def generate_incident_report(self, events: List[Dict[str, Any]]) -> str:
        """Generate incident report"""
    
    async def predict_next_attack(self, historical_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict next attack"""
    
    async def generate_playbook_recommendation(self, available_playbooks: List[str]) -> str:
        """Generate playbook recommendation"""

# backend/app/services/anomaly_detector.py
"""
Multi-algorithm anomaly detection:
- Isolation Forest (fast, scalable)
- Local Outlier Factor (density-based)
- Autoencoder (neural network)
- Ensemble voting
"""

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging
from datetime import datetime, timedelta
import pickle
import json

logger = logging.getLogger(__name__)

class AnomalyDetectorService:
    """
    Multi-algorithm anomaly detection system
    """
    
    def __init__(self, db, cache):
        self.db = db
        self.total_samples = 0
    
    async def load_models(self):
        """Load pre-trained models"""
    
    def _extract_features(self, event: Dict[str, Any]) -> np.ndarray:
        """Extract ML features from event"""
    
    async def train(self, historical_events: List[Dict[str, Any]]):
        """Train anomaly detection models"""
    
    async def detect(self, detection_threshold: float = 0.75) -> Tuple[bool, float, str]:
        """Detect anomalies"""
    
    async def detect_batch(self, events: List[Dict[str, Any]]) -> List[Tuple[str, bool, float]]:
        """Detect anomalies in batch"""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get anomaly detection statistics"""

# backend/app/services/risk_scorer.py
"""
Advanced risk scoring algorithm
CVSS-inspired with additional factors
"""

from typing import Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RiskScorer:
    """
    Multi-factor risk scoring system (0-100)
    """
    
    # Risk weights
    WEIGHTS = {
        "severity": 0.25,
        "anomaly_score": 0.10,
    }
    
    SEVERITY_SCORES = {
        "CRITICAL": 10,
        "INFO": 0
    }
    
    async def calculate_risk_score(self, event: Dict[str, Any]) -> int:
        """Calculate risk score"""
    
    def get_risk_level(self, score: int) -> str:
        """Convert score to risk level"""

# backend/app/main.py
"""
Main entry point for the FastAPI application
"""

from fastapi import FastAPI
from app.core.cache import CacheManager
from app.core.event_bus import init_event_bus
from app.core.security import SecurityManager

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    # Initialize cache, event bus, and security manager

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    # Cleanup resources

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Cybersecurity SOC"}

# frontend/src/pages/Dashboard.tsx
import React, { useEffect, useState, useCallback } from 'react';
import { useQuery } from 'react-query';
import { useWebSocket } from '../hooks/useWebSocket';
import { useAuth } from '../hooks/useAuth';
import Header from '../components/Header';
import ThreatMap from '../components/ThreatMap';
import RiskScoreCard from '../components/RiskScoreCard';
import AttackTimeline from '../components/AttackTimeline';
import AIAnalyst from '../components/AIAnalyst';
import ThreatTempo from '../components/ThreatTempo';
import AlertTable from '../components/AlertTable';
import IncidentPanel from '../components/IncidentPanel';
import SearchBar from '../components/SearchBar';
import StatisticCard from '../components/StatisticCard';

interface DashboardState {
  selectedEvent: any;
  riskScore: number;
}

export default function Dashboard() {
  const { user } = useAuth();
  const { data: liveData, isConnected } = useWebSocket('/ws/dashboard');
  const [state, setState] = useState<DashboardState>({
    selectedEvent: null,
    riskScore: 0,
  });

  const { data: stats } = useQuery('systemStats', () =>
    fetch('/api/v1/system/stats').then(r => r.json()),
    { refetchInterval: 5000 }
  );

  useEffect(() => {
    if (liveData && Array.isArray(liveData)) {
      // Handle live data
    }
  }, [liveData, stats]);

  const handleSelectEvent = useCallback((event: any) => {
    setState(prev => ({ ...prev, selectedEvent: event }));
  }, []);

  return (
    <div>
      <Header />
      <ThreatMap events={liveData} />
      <RiskScoreCard score={state.riskScore} />
      {/* Other components */}
    </div>
  );
}

# frontend/src/components/ThreatMap.tsx
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface ThreatMapProps {
  events: any[];
}

export default function ThreatMap({ events }: ThreatMapProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || events.length === 0) return;
    // D3 rendering logic
  }, [events]);

  return <svg ref={svgRef}></svg>;
}

# frontend/package.json
{
  "name": "cybersecurity-soc",
  "version": "1.0.0",
  "description": "Cybersecurity Operations Center Application",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-query": "^3.39.2",
    "d3": "^7.6.1"
  },
  "devDependencies": {
    "@types/react": "^18.0.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test"
  }
}

# backend/requirements.txt
fastapi
uvicorn
redis
aiokafka
jose
passlib
pydantic
openai
scikit-learn
tenacity

# frontend/src/hooks/useWebSocket.ts
import { useEffect, useState } from 'react';

export function useWebSocket(url: string) {
  const [data, setData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socket = new WebSocket(url);
    socket.onopen = () => setIsConnected(true);
    socket.onmessage = (event) => {
      const parsedData = JSON.parse(event.data);
      setData(parsedData);
    };
    socket.onclose = () => setIsConnected(false);
    return () => socket.close();
  }, [url]);

  return { data, isConnected };
}

# frontend/src/hooks/useAuth.ts
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

export function useAuth() {
  return useContext(AuthContext);
}
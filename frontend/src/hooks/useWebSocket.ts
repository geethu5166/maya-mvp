import { useEffect, useState, useRef } from 'react';

interface WebSocketMessage {
  type: string;
  data: any;
}

export function useWebSocket(url: string, onMessage?: (message: WebSocketMessage) => void) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      const wsUrl = `${url}?token=${token}`;
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        setConnected(true);
        setError(null);
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          onMessage?.(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.current.onerror = () => {
        setError('WebSocket connection error');
      };

      ws.current.onclose = () => {
        setConnected(false);
      };

      return () => {
        ws.current?.close();
      };
    } catch (err: any) {
      setError(err.message);
    }
  }, [url, onMessage]);

  const send = (message: WebSocketMessage) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    }
  };

  return { connected, error, send };
}
        - Header.tsx
        - IncidentPanel.tsx
        - RiskScoreCard.tsx
        - SearchBar.tsx
        - StatisticCard.tsx
        - ThreatMap.tsx
        - ThreatTempo.tsx
      - pages/
        - Dashboard.tsx
      - hooks/
        - useAuth.ts
        - useWebSocket.ts
      - utils/
        - classnames.ts
      - App.tsx
      - index.tsx
    - package.json
    - vite.config.ts

# Backend Implementation

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

# Decorator for caching function results
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

# Global event bus instance
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

# Password hashing
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
    # Initialize cache and event bus
    pass

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    # Cleanup resources
    pass

# Frontend Implementation

# frontend/package.json
{
  "name": "cybersecurity-soc",
  "version": "1.0.0",
  "description": "Cybersecurity Operations Center Dashboard",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-query": "^3.39.2",
    "framer-motion": "^4.1.17",
    "d3": "^7.6.1"
  },
  "devDependencies": {
    "@types/react": "^18.0.0",
    "@testing-library/react": "^12.1.5"
  },
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "serve": "vite preview"
  }
}

# frontend/src/App.tsx
import React from 'react';
import Dashboard from './pages/Dashboard';

const App = () => {
  return (
    <div>
      <Dashboard />
    </div>
  );
};

export default App;

# frontend/src/index.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

# frontend/src/pages/Dashboard.tsx
import React, { useEffect, useState } from 'react';
import { useQuery } from 'react-query';
import Header from '../components/Header';
import ThreatMap from '../components/ThreatMap';
import RiskScoreCard from '../components/RiskScoreCard';
import AlertTable from '../components/AlertTable';

const Dashboard = () => {
  const { data: stats } = useQuery('systemStats', () =>
    fetch('/api/v1/system/stats').then(res => res.json())
  );

  return (
    <div>
      <Header />
      <ThreatMap events={stats?.events} />
      <RiskScoreCard score={stats?.riskScore} />
      <AlertTable alerts={stats?.alerts} />
    </div>
  );
};

export default Dashboard;

# frontend/src/components/Header.tsx
import React from 'react';

const Header = () => {
  return (
    <header>
      <h1>Cybersecurity Operations Center</h1>
    </header>
  );
};

export default Header;

# frontend/src/components/ThreatMap.tsx
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface ThreatMapProps {
  events: any[];
}

const ThreatMap: React.FC<ThreatMapProps> = ({ events }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || events.length === 0) return;
    // D3 rendering logic here
  }, [events]);

  return <svg ref={svgRef}></svg>;
};

export default ThreatMap;

# frontend/src/components/RiskScoreCard.tsx
import React from 'react';

interface RiskScoreCardProps {
  score: number;
}

const RiskScoreCard: React.FC<RiskScoreCardProps> = ({ score }) => {
  return (
    <div>
      <h2>Risk Score: {score}</h2>
    </div>
  );
};

export default RiskScoreCard;

# frontend/src/components/AlertTable.tsx
import React from 'react';

interface AlertTableProps {
  alerts: any[];
}

const AlertTable: React.FC<AlertTableProps> = ({ alerts }) => {
  return (
    <table>
      <thead>
        <tr>
          <th>Alert ID</th>
          <th>Severity</th>
          <th>Message</th>
        </tr>
      </thead>
      <tbody>
        {alerts.map(alert => (
          <tr key={alert.id}>
            <td>{alert.id}</td>
            <td>{alert.severity}</td>
            <td>{alert.message}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

export default AlertTable;
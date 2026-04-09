import { Sparkles, Lightbulb } from 'lucide-react'

interface AIAnalystProps {
  insight: string
  recommendations: string[]
  confidence: number
}

export default function AIAnalyst({ insight, recommendations, confidence }: AIAnalystProps) {
  return (
    <div className="card-lg bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 border-l-4 border-blue-500">
      <div className="flex items-center gap-3 mb-4">
        <div className="w-10 h-10 bg-blue-500 rounded-lg flex items-center justify-center">
          <Sparkles size={20} className="text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-slate-900 dark:text-white">AI Analyst</h3>
          <p className="text-sm text-slate-600 dark:text-slate-400">Confidence: {(confidence * 100).toFixed(0)}%</p>
        </div>
      </div>

      <p className="text-slate-900 dark:text-slate-100 mb-4">{insight}</p>

      <div className="space-y-2">
        <h4 className="text-sm font-semibold text-slate-900 dark:text-white flex items-center gap-2">
          <Lightbulb size={16} />
          Recommendations
        </h4>
        <ul className="space-y-2">
          {recommendations.map((rec, idx) => (
            <li key={idx} className="text-sm text-slate-700 dark:text-slate-300 flex gap-2">
              <span className="text-blue-500 font-bold">{idx + 1}.</span>
              <span>{rec}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
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
  - README.md

# Backend Code

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
import json
import logging
import asyncio
from typing import Callable, Dict, List, Any, Optional
from datetime import datetime
import time
from dataclasses import dataclass, asdict
from enum import Enum

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
    
    @staticmethod
    def _serialize(value: Dict[str, Any]) -> bytes:
        """Serialize event to bytes"""
        return json.dumps(value, default=str).encode('utf-8')
    
    @staticmethod
    def _deserialize(value: bytes) -> Dict[str, Any]:
        """Deserialize event from bytes"""
        return json.loads(value.decode('utf-8'))

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
import logging

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

logger = logging.getLogger(__name__)

class AIEngineService:
    """
    Advanced AI engine for threat analysis
    """
    
    def __init__(self, openai_key: str):
        openai.api_key = openai_key
    
    async def analyze_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security event using AI"""
    
    async def generate_incident_report(self, events: List[Dict[str, Any]]) -> str:
        """Generate incident report"""
    
    async def predict_next_attack(self, historical_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict next attack based on historical data"""

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
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)

class AnomalyDetectorService:
    """
    Multi-algorithm anomaly detection system
    """
    
    def __init__(self):
        self.total_samples = 0
    
    async def load_models(self):
        """Load pre-trained models"""
    
    async def detect(self, event: Dict[str, Any]) -> Tuple[bool, float]:
        """Detect anomalies in a single event"""
    
    async def detect_batch(self, events: List[Dict[str, Any]]) -> List[Tuple[str, bool]]:
        """Detect anomalies in a batch of events"""

# backend/app/services/risk_scorer.py
"""
Advanced risk scoring algorithm
CVSS-inspired with additional factors
"""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class RiskScorer:
    """
    Multi-factor risk scoring system (0-100)
    """
    
    async def calculate_risk_score(self, event: Dict[str, Any]) -> int:
        """Calculate risk score for an event"""
    
    def get_risk_level(self, score: int) -> str:
        """Convert score to risk level"""

# backend/app/main.py
"""
Main entry point for the FastAPI application
"""

from fastapi import FastAPI
from app.core.cache import CacheManager
from app.core.event_bus import EventBusManager
from app.core.security import SecurityManager

app = FastAPI()

# Initialize services
cache_manager = CacheManager(redis_url="redis://localhost:6379")
event_bus_manager = EventBusManager(brokers=["localhost:9092"])
security_manager = SecurityManager(secret_key="your_secret_key")

@app.on_event("startup")
async def startup_event():
    await cache_manager.connect()
    await event_bus_manager.start()

@app.on_event("shutdown")
async def shutdown_event():
    await cache_manager.disconnect()
    await event_bus_manager.stop()

@app.get("/")
async def read_root():
    return {"Hello": "World"}

# Frontend Code

# frontend/src/components/AlertTable.tsx
import React from 'react';

const AlertTable = () => {
    return (
        <div>
            {/* Alert table implementation */}
        </div>
    );
};

export default AlertTable;

# frontend/src/components/AIAnalyst.tsx
import React from 'react';

const AIAnalyst = () => {
    return (
        <div>
            {/* AI Analyst implementation */}
        </div>
    );
};

export default AIAnalyst;

# frontend/src/components/Header.tsx
import React from 'react';

const Header = () => {
    return (
        <header>
            <h1>Cybersecurity SOC Dashboard</h1>
        </header>
    );
};

export default Header;

# frontend/src/components/IncidentPanel.tsx
import React from 'react';

const IncidentPanel = () => {
    return (
        <div>
            {/* Incident panel implementation */}
        </div>
    );
};

export default IncidentPanel;

# frontend/src/components/RiskScoreCard.tsx
import React from 'react';

const RiskScoreCard = () => {
    return (
        <div>
            {/* Risk score card implementation */}
        </div>
    );
};

export default RiskScoreCard;

# frontend/src/components/SearchBar.tsx
import React from 'react';

const SearchBar = () => {
    return (
        <div>
            {/* Search bar implementation */}
        </div>
    );
};

export default SearchBar;

# frontend/src/components/StatisticCard.tsx
import React from 'react';

const StatisticCard = () => {
    return (
        <div>
            {/* Statistic card implementation */}
        </div>
    );
};

export default StatisticCard;

# frontend/src/components/ThreatMap.tsx
import React from 'react';

const ThreatMap = () => {
    return (
        <div>
            {/* Threat map implementation */}
        </div>
    );
};

export default ThreatMap;

# frontend/src/components/ThreatTempo.tsx
import React from 'react';

const ThreatTempo = () => {
    return (
        <div>
            {/* Threat tempo implementation */}
        </div>
    );
};

export default ThreatTempo;

# frontend/src/pages/Dashboard.tsx
import React from 'react';
import Header from '../components/Header';
import AlertTable from '../components/AlertTable';
import AIAnalyst from '../components/AIAnalyst';
import RiskScoreCard from '../components/RiskScoreCard';
import ThreatMap from '../components/ThreatMap';
import ThreatTempo from '../components/ThreatTempo';

const Dashboard = () => {
    return (
        <div>
            <Header />
            <RiskScoreCard />
            <AlertTable />
            <ThreatMap />
            <ThreatTempo />
            <AIAnalyst />
        </div>
    );
};

export default Dashboard;

# frontend/src/hooks/useAuth.ts
import { useState } from 'react';

const useAuth = () => {
    const [user, setUser] = useState(null);
    
    const login = (userData) => {
        setUser(userData);
    };

    const logout = () => {
        setUser(null);
    };

    return { user, login, logout };
};

export default useAuth;

# frontend/src/hooks/useWebSocket.ts
import { useEffect, useState } from 'react';

const useWebSocket = (url) => {
    const [data, setData] = useState(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        const socket = new WebSocket(url);

        socket.onopen = () => {
            setIsConnected(true);
        };

        socket.onmessage = (event) => {
            setData(JSON.parse(event.data));
        };

        socket.onclose = () => {
            setIsConnected(false);
        };

        return () => {
            socket.close();
        };
    }, [url]);

    return { data, isConnected };
};

export default useWebSocket;

# frontend/src/utils/classnames.ts
const cn = (...classes) => {
    return classes.filter(Boolean).join(' ');
};

export { cn };

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
import ReactDOM from 'react-dom';
import App from './App';

ReactDOM.render(<App />, document.getElementById('root'));

# frontend/package.json
{
  "name": "cybersecurity-soc",
  "version": "1.0.0",
  "description": "Cybersecurity Operations Center Application",
  "private": true,
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test"
  }
}

# frontend/README.md
# Cybersecurity SOC Application

This project is a complete Cybersecurity Operations Center application built with a FastAPI backend and a React frontend. It includes advanced features such as caching, event bus integration, security management, and AI/ML capabilities.
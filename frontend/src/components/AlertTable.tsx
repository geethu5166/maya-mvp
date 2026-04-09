import { SecurityEvent } from '../types'
import { ChevronRight, Zap, Search } from 'lucide-react'
import { getSeverityBadgeColor, formatDate, getTimeAgo } from '../utils/classnames'
import { useState } from 'react'

interface AlertTableProps {
  events: SecurityEvent[]
  onSelectEvent?: (event: SecurityEvent) => void
  loading?: boolean
}

export default function AlertTable({ events, onSelectEvent, loading = false }: AlertTableProps) {
  const [filter, setFilter] = useState('')
  const [sortBy, setSortBy] = useState<'time' | 'severity'>('time')

  const filteredEvents = events.filter(e =>
    e.event_type.toLowerCase().includes(filter.toLowerCase()) ||
    e.user?.toLowerCase().includes(filter.toLowerCase()) ||
    e.asset?.toLowerCase().includes(filter.toLowerCase())
  )

  const sortedEvents = [...filteredEvents].sort((a, b) => {
    if (sortBy === 'time') {
      return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    } else {
      const severityOrder = { 'CRITICAL': 5, 'HIGH': 4, 'MEDIUM': 3, 'LOW': 2, 'INFO': 1 }
      return (severityOrder[b.severity as keyof typeof severityOrder] || 0) -
             (severityOrder[a.severity as keyof typeof severityOrder] || 0)
    }
  })

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-slate-200 dark:border-slate-800">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Security Events</h2>
        <span className="text-sm bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-3 py-1 rounded-full">
          {events.length} events
        </span>
      </div>

      {/* Filters */}
      <div className="p-6 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-4">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search events..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="input-field pl-10"
            />
          </div>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="input-field"
          >
            <option value="time">Newest First</option>
            <option value="severity">Highest Severity</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/50">
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-400">Type</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-400">Severity</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-400">Asset</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-400">User</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 dark:text-slate-400">Time</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-slate-600 dark:text-slate-400">Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                  Loading events...
                </td>
              </tr>
            ) : sortedEvents.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-6 py-8 text-center text-slate-500">
                  No events found
                </td>
              </tr>
            ) : (
              sortedEvents.map((event) => (
                <tr
                  key={event.event_id}
                  className="table-row cursor-pointer"
                  onClick={() => onSelectEvent?.(event)}
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <Zap size={16} className="text-yellow-500" />
                      <code className="text-sm font-mono text-slate-600 dark:text-slate-400">
                        {event.event_type.replace(/_/g, ' ')}
                      </code>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`badge-threat ${getSeverityBadgeColor(event.severity)}`}>
                      {event.severity}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-900 dark:text-slate-100">
                    {event.asset || '—'}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-900 dark:text-slate-100">
                    {event.user || '—'}
                  </td>
                  <td className="px-6 py-4 text-sm text-slate-500 dark:text-slate-400">
                    <div className="flex flex-col">
                      <span>{getTimeAgo(event.timestamp)}</span>
                      <span className="text-xs">{formatDate(event.timestamp)}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">
                      <ChevronRight size={18} className="text-slate-400" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
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
        - AttackTimeline.tsx
      - hooks/
        - useAuth.ts
        - useWebSocket.ts
      - pages/
        - Dashboard.tsx
      - utils/
        - classnames.ts
    - package.json
    - vite.config.ts

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
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None
    ) -> bool:
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
            key = f"{key_prefix}:{args}:{kwargs}"
            cached_value = await cache_manager.get(key)
            if cached_value is not None:
                return cached_value
            result = await func(*args, **kwargs)
            await cache_manager.set(key, result, ttl_seconds)
            return result
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
    
    async def publish_event(
        self,
        event: SecurityEvent
    ) -> bool:
        """Publish an event to Kafka"""
    
    async def subscribe(
        self,
        callback: Callable[[Dict[str, Any]], None]
    ):
        """Subscribe to events"""
    
    async def _consume_messages(
        self,
        callback: Callable
    ):
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
    
    def __init__(
        self,
        secret_key: str,
        refresh_token_expire_days: int = 7,
    ):
        self.secret_key = secret_key
        self.refresh_token_expire_days = refresh_token_expire_days
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_token(
        self,
        expires_delta: Optional[timedelta] = None
    ) -> str:
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
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def analyze_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security event"""
    
    async def generate_incident_report(
        self,
        events: List[Dict[str, Any]]
    ) -> str:
        """Generate incident report"""
    
    async def predict_next_attack(
        self,
        historical_events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Predict next attack"""
    
    async def generate_playbook_recommendation(
        self,
        available_playbooks: List[str]
    ) -> str:
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
    
    async def detect(
        self,
        detection_threshold: float = 0.75
    ) -> Tuple[bool, float, str]:
        """Detect anomalies"""
    
    async def detect_batch(
        self,
        events: List[Dict[str, Any]]
    ) -> List[Tuple[str, bool, float]]:
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

# Initialize components
cache_manager = CacheManager(redis_url="redis://localhost:6379")
event_bus = init_event_bus(brokers=["localhost:9092"])
security_manager = SecurityManager(secret_key="your_secret_key")

@app.on_event("startup")
async def startup_event():
    await cache_manager.connect()
    await event_bus.start()

@app.on_event("shutdown")
async def shutdown_event():
    await cache_manager.disconnect()
    await event_bus.stop()

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
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-900 to-slate-950">
      <Header />
      <ThreatMap events={liveData} />
      <RiskScoreCard score={state.riskScore} />
      <AttackTimeline />
      <AIAnalyst />
      <ThreatTempo />
      <AlertTable />
      <IncidentPanel />
      <SearchBar />
      <StatisticCard stats={stats} />
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
    "react-query": "^3.34.0",
    "d3": "^7.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.0.0",
    "@testing-library/react": "^12.0.0"
  },
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "serve": "vite preview"
  }
}

# frontend/vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
  },
});
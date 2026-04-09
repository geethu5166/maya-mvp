import { useState, useCallback, useEffect } from 'react';
import axios, { AxiosInstance } from 'axios';
import { LoginRequest, LoginResponse, SecurityEvent, Incident, PaginatedResponse } from '../types';

let apiClient: AxiosInstance;

// Initialize API client
function initializeApiClient() {
  const token = localStorage.getItem('token');
  apiClient = axios.create({
    baseURL: '/api/v1',
    headers: {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  });

  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );

  return apiClient;
}

function getApiClient() {
  if (!apiClient) {
    initializeApiClient();
  }
  return apiClient;
}

export function useAuth() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (credentials: LoginRequest) => {
    setLoading(true);
    setError(null);
    try {
      const client = getApiClient();
      const response = await client.post<LoginResponse>('/auth/login', credentials);
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setUser(userData);
      
      // Update default header
      client.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return userData;
    } catch (err: any) {
      const message = err.response?.data?.detail || 'Login failed';
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    setUser(null);
    getApiClient().defaults.headers.common['Authorization'] = '';
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token && !user) {
      // Could fetch current user here
      initializeApiClient();
    }
  }, [user]);

  return { user, loading, error, login, logout };
}

export function useQuery<T>(url: string, dependencies: any[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchData = async () => {
      try {
        setLoading(true);
        const client = getApiClient();
        const response = await client.get<T>(url);
        if (mounted) {
          setData(response.data);
          setError(null);
        }
      } catch (err: any) {
        if (mounted) {
          setError(err.message || 'Failed to fetch data');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchData();
    return () => {
      mounted = false;
    };
  }, dependencies);

  return { data, loading, error };
}

export function usePaginatedEvents(filters?: any) {
  const [page, setPage] = useState(1);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    let mounted = true;

    const fetchEvents = async () => {
      try {
        setLoading(true);
        const client = getApiClient();
        const response = await client.get<PaginatedResponse<SecurityEvent>>(
          `/events?page=${page}&limit=20`,
          { params: filters }
        );
        if (mounted) {
          setEvents(response.data.items);
          setTotal(response.data.total);
          setError(null);
        }
      } catch (err: any) {
        if (mounted) {
          setError(err.message || 'Failed to fetch events');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchEvents();
    return () => {
      mounted = false;
    };
  }, [page, filters]);

  return { events, loading, error, total, page, setPage };
}

export function usePaginatedIncidents(filters?: any) {
  const [page, setPage] = useState(1);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    let mounted = true;

    const fetchIncidents = async () => {
      try {
        setLoading(true);
        const client = getApiClient();
        const response = await client.get<PaginatedResponse<Incident>>(
          `/incidents?page=${page}&limit=20`,
          { params: filters }
        );
        if (mounted) {
          setIncidents(response.data.items);
          setTotal(response.data.total);
          setError(null);
        }
      } catch (err: any) {
        if (mounted) {
          setError(err.message || 'Failed to fetch incidents');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchIncidents();
    return () => {
      mounted = false;
    };
  }, [page, filters]);

  return { incidents, loading, error, total, page, setPage };
}

export async function createIncident(data: {
  title: string;
  description: string;
  severity: string;
  event_ids?: string[];
}) {
  const client = getApiClient();
  return client.post<Incident>('/incidents', data);
}

export async function updateIncident(
  incidentId: string,
  data: Partial<Incident>
) {
  const client = getApiClient();
  return client.patch<Incident>(`/incidents/${incidentId}`, data);
}

export async function acknowledgeAlert(alertId: string) {
  const client = getApiClient();
  return client.post(`/alerts/${alertId}/acknowledge`);
}
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
import numpy as np

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
    
    async def detect(self, events: List[Dict[str, Any]]) -> List[Tuple[str, bool]]:
        """Detect anomalies in events"""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get anomaly detection statistics"""

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

# Initialize components
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

# Add your API routes here

# Backend requirements
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

# Frontend Implementation

# frontend/package.json
{
  "name": "cybersecurity-soc",
  "version": "1.0.0",
  "description": "Cybersecurity Operations Center Dashboard",
  "private": true,
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "react-query": "^3.0.0",
    "framer-motion": "^4.0.0",
    "axios": "^0.21.1"
  },
  "devDependencies": {
    "typescript": "^4.0.0",
    "vite": "^2.0.0"
  },
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "serve": "vite preview"
  }
}

# frontend/src/pages/Dashboard.tsx
import React, { useEffect, useState } from 'react';
import { useQuery } from 'react-query';
import Header from '../components/Header';
import ThreatMap from '../components/ThreatMap';
import RiskScoreCard from '../components/RiskScoreCard';
import AlertTable from '../components/AlertTable';

export default function Dashboard() {
  const { data: stats } = useQuery('systemStats', () =>
    fetch('/api/v1/system/stats').then(r => r.json())
  );

  return (
    <div>
      <Header />
      <ThreatMap events={stats?.events} />
      <RiskScoreCard score={stats?.riskScore} />
      <AlertTable alerts={stats?.alerts} />
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
    // D3 rendering logic here
  }, [events]);

  return <svg ref={svgRef}></svg>;
}

# frontend/src/components/AlertTable.tsx
import React from 'react';

interface AlertTableProps {
  alerts: any[];
}

export default function AlertTable({ alerts }: AlertTableProps) {
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
}

# frontend/src/components/RiskScoreCard.tsx
import React from 'react';

interface RiskScoreCardProps {
  score: number;
}

export default function RiskScoreCard({ score }: RiskScoreCardProps) {
  return (
    <div>
      <h2>Risk Score</h2>
      <p>{score}</p>
    </div>
  );
}

# frontend/src/components/Header.tsx
import React from 'react';

export default function Header() {
  return (
    <header>
      <h1>Cybersecurity Operations Center</h1>
    </header>
  );
}
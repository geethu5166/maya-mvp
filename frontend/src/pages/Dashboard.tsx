import { useState, useEffect } from 'react'
import { usePaginatedEvents, useQuery } from '../hooks/useQuery'
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import AlertTable from '../components/AlertTable'
import RiskScoreCard from '../components/RiskScoreCard'
import AIAnalyst from '../components/AIAnalyst'
import ThreatMap from '../components/ThreatMap'
import { TrendingUp, Activity, AlertTriangle, Shield } from 'lucide-react'

export default function Dashboard() {
  const { events, loading } = usePaginatedEvents()
  const [selectedEvent, setSelectedEvent] = useState(null)

  // Sample data for charts
  const trendData = [
    { time: '00:00', alerts: 12, incidents: 3 },
    { time: '04:00', alerts: 19, incidents: 5 },
    { time: '08:00', alerts: 25, incidents: 7 },
    { time: '12:00', alerts: 42, incidents: 12 },
    { time: '16:00', alerts: 31, incidents: 8 },
    { time: '20:00', alerts: 28, incidents: 6 },
  ]

  const severityData = [
    { name: 'Critical', value: 12, color: '#dc2626' },
    { name: 'High', value: 24, color: '#ea580c' },
    { name: 'Medium', value: 45, color: '#f59e0b' },
    { name: 'Low', value: 19, color: '#10b981' },
  ]

  const threatsByCountry = [
    { country: 'China', count: 124, severity: 'CRITICAL' },
    { country: 'Russia', count: 89, severity: 'HIGH' },
    { country: 'Unknown', count: 56, severity: 'MEDIUM' },
    { country: 'Brazil', count: 34, severity: 'LOW' },
  ]

  return (
    <div className="p-8 space-y-8">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Total Events</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-white">2,847</p>
            </div>
            <Activity size={40} className="text-blue-500 opacity-20" />
          </div>
          <p className="text-xs text-green-600 mt-2">↑ 12% from yesterday</p>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Critical Alerts</p>
              <p className="text-3xl font-bold text-red-600">12</p>
            </div>
            <AlertTriangle size={40} className="text-red-500 opacity-20" />
          </div>
          <p className="text-xs text-red-600 mt-2">↑ 3 new this hour</p>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Active Incidents</p>
              <p className="text-3xl font-bold text-orange-600">8</p>
            </div>
            <TrendingUp size={40} className="text-orange-500 opacity-20" />
          </div>
          <p className="text-xs text-orange-600 mt-2">Avg MTTR: 2.5h</p>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400">Detection Rate</p>
              <p className="text-3xl font-bold text-green-600">95.8%</p>
            </div>
            <Shield size={40} className="text-green-500 opacity-20" />
          </div>
          <p className="text-xs text-green-600 mt-2">↑ 2.1% this month</p>
        </div>
      </div>

      {/* Risk Scores */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <RiskScoreCard score={72} trend={5} title="Overall Risk" subtitle="Enterprise-wide assessment" />
        <RiskScoreCard score={85} trend={12} title="Network Risk" subtitle="Last 24 hours" />
        <RiskScoreCard score={45} trend={-8} title="Application Risk" subtitle="Improving trend" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Trend Chart */}
        <div className="card-lg">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Alert Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="time" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="alerts" stroke="#3b82f6" strokeWidth={2} />
              <Line type="monotone" dataKey="incidents" stroke="#ef4444" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Severity Distribution */}
        <div className="card-lg">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Severity Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={severityData}
                cx="50%"
                cy="50%"
                innerRadius={80}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {severityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* AI Analyst Insight */}
      <AIAnalyst
        insight="Detected coordinated scanning activity from 3 distinct geographic locations targeting your database servers. This pattern matches known reconnaissance behavior from APT28. Recommend immediate network segmentation and credential rotation for database administrators."
        recommendations={[
          'Isolate database servers to restricted VLANs',
          'Rotate all database administrator credentials',
          'Enable enhanced logging for database access',
          'Deploy IDS signatures for APT28 attack patterns',
        ]}
        confidence={0.92}
      />

      {/* Threat Map */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ThreatMap threats={threatsByCountry} />

        {/* Top Detection Rules */}
        <div className="card-lg">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">Top Detection Rules</h3>
          <div className="space-y-3">
            {[
              { rule: 'SSH Brute Force Detection', triggered: 234, confidence: 98 },
              { rule: 'Unusual Data Transfer', triggered: 156, confidence: 92 },
              { rule: 'Privilege Escalation', triggered: 89, confidence: 88 },
            ].map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-slate-900 dark:text-white">{item.rule}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">{item.triggered}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{item.confidence}% confidence</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Events */}
      <AlertTable events={events} onSelectEvent={setSelectedEvent} loading={loading} />
    </div>
  )
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
    SECURITY_EVENT = "SECURITY_EVENT"

@dataclass
class SecurityEvent:
    """Standard security event schema"""
    event_id: str
    event_type: EventType
    timestamp: datetime
    details: Dict[str, Any]

class EventBusManager:
    """
    Advanced Kafka-based event bus
    - High-throughput event ingestion
    - Guaranteed delivery
    """
    
    def __init__(self, brokers: List[str]):
        self.brokers = brokers
    
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

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Token(BaseModel):
    """Token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

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
    
    def create_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT token"""
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify JWT token"""

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
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class AIEngineService:
    """
    Advanced AI engine for threat analysis
    """
    
    def __init__(self, openai_key: str):
        openai.api_key = openai_key
    
    async def analyze_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze security event using AI models"""
    
    async def generate_incident_report(self, events: List[Dict[str, Any]]) -> str:
        """Generate incident report based on events"""

# backend/app/services/anomaly_detector.py
"""
Multi-algorithm anomaly detection:
- Isolation Forest (fast, scalable)
- Local Outlier Factor (density-based)
- Autoencoder (neural network)
"""

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
import numpy as np
from typing import List, Dict

class AnomalyDetectorService:
    """
    Multi-algorithm anomaly detection system
    """
    
    def __init__(self):
        self.models = {
            "isolation_forest": IsolationForest(),
            "local_outlier_factor": LocalOutlierFactor()
        }
    
    async def detect(self, data: List[Dict[str, Any]]) -> List[bool]:
        """Detect anomalies in the provided data"""
    
    async def train(self, historical_data: List[Dict[str, Any]]):
        """Train anomaly detection models"""

# backend/app/services/risk_scorer.py
"""
Advanced risk scoring algorithm
CVSS-inspired with additional factors
"""

from typing import Dict

class RiskScorer:
    """
    Multi-factor risk scoring system (0-100)
    """
    
    def calculate_risk_score(self, event: Dict[str, Any]) -> int:
        """Calculate risk score based on event attributes"""

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
            {/* AI Analyst component implementation */}
        </div>
    );
};

export default AIAnalyst;

# frontend/src/components/Header.tsx
import React from 'react';

const Header = () => {
    return (
        <header>
            {/* Header implementation */}
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

# frontend/src/hooks/useAuth.ts
import { useState } from 'react';

const useAuth = () => {
    const [user, setUser] = useState(null);
    return { user, setUser };
};

export default useAuth;

# frontend/src/hooks/useWebSocket.ts
import { useEffect, useState } from 'react';

const useWebSocket = (url) => {
    const [data, setData] = useState(null);
    const [isConnected, setIsConnected] = useState(false);

    useEffect(() => {
        const socket = new WebSocket(url);
        socket.onopen = () => setIsConnected(true);
        socket.onmessage = (event) => setData(JSON.parse(event.data));
        socket.onclose = () => setIsConnected(false);
        return () => socket.close();
    }, [url]);

    return { data, isConnected };
};

export default useWebSocket;

# frontend/src/pages/Dashboard.tsx
import React from 'react';

const Dashboard = () => {
    return (
        <div>
            {/* Dashboard implementation */}
        </div>
    );
};

export default Dashboard;

# frontend/src/utils/classnames.ts
const cn = (...classes) => classes.filter(Boolean).join(' ');

export { cn };

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

# backend/requirements.txt
fastapi
uvicorn
redis
aiokafka
jose
passlib
pydantic
scikit-learn
openai
```
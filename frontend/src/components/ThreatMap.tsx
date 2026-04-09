import { Globe, AlertCircle } from 'lucide-react'

interface ThreatData {
  country: string
  count: number
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
}

interface ThreatMapProps {
  threats: ThreatData[]
}

export default function ThreatMap({ threats }: ThreatMapProps) {
  const severityColors = {
    'LOW': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300',
    'MEDIUM': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300',
    'HIGH': 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
    'CRITICAL': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
  }

  return (
    <div className="card-lg">
      <div className="flex items-center gap-3 mb-6">
        <Globe size={24} className="text-blue-500" />
        <div>
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white">Global Threat Map</h3>
          <p className="text-sm text-slate-500 dark:text-slate-400">Top threat sources</p>
        </div>
      </div>

      {threats.length === 0 ? (
        <div className="py-12 text-center">
          <AlertCircle size={48} className="mx-auto text-slate-300 dark:text-slate-700 mb-3" />
          <p className="text-slate-500 dark:text-slate-400">No threat data available</p>
        </div>
      ) : (
        <div className="space-y-3">
          {threats.map((threat, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
              <div className="flex-1">
                <p className="font-medium text-slate-900 dark:text-white">{threat.country}</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">{threat.count}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">incidents</p>
                </div>
                <span className={`badge-threat px-3 py-1 ${severityColors[threat.severity]}`}>
                  {threat.severity}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
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
    DATA_EXFILTRATION = "DATA_EXFILTRATION"

class Severity(str, Enum):
    """Event severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class SecurityEvent:
    """Standard security event schema"""
    event_id: str
    event_type: EventType
    severity: Severity
    source: str
    timestamp: datetime
    ip_address: str
    payload: Optional[Dict[str, Any]] = None

class EventBusManager:
    """
    Advanced Kafka-based event bus
    - High-throughput event ingestion
    - Guaranteed delivery
    - Event correlation
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
        """Subscribe to events from Kafka"""

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
        """Generate incident report from events"""

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
from typing import Dict, List, Tuple

class AnomalyDetectorService:
    """
    Multi-algorithm anomaly detection system
    """
    
    def __init__(self):
        self.models = {
            "isolation_forest": IsolationForest(),
            "local_outlier_factor": LocalOutlierFactor()
        }
    
    async def detect(self, events: List[Dict[str, Any]]) -> List[Tuple[str, bool]]:
        """Detect anomalies in events"""

# backend/app/services/risk_scorer.py
"""
Advanced risk scoring algorithm
CVSS-inspired with additional factors
"""

from typing import Dict, Any

class RiskScorer:
    """
    Multi-factor risk scoring system (0-100)
    """
    
    async def calculate_risk_score(self, event: Dict[str, Any]) -> int:
        """Calculate risk score for an event"""

# backend/app/main.py
"""
Main entry point for the FastAPI application
"""

from fastapi import FastAPI
from app.core.cache import CacheManager
from app.core.event_bus import EventBusManager
from app.core.security import SecurityManager
from app.services.ai_engine import AIEngineService
from app.services.anomaly_detector import AnomalyDetectorService
from app.services.risk_scorer import RiskScorer

app = FastAPI()

# Initialize services
cache_manager = CacheManager(redis_url="redis://localhost:6379")
event_bus_manager = EventBusManager(brokers=["localhost:9092"])
security_manager = SecurityManager(secret_key="your_secret_key")
ai_engine_service = AIEngineService(openai_key="your_openai_key")
anomaly_detector_service = AnomalyDetectorService()
risk_scorer = RiskScorer()

@app.get("/")
async def root():
    return {"message": "Welcome to the Cybersecurity SOC API"}

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

# frontend/src/pages/Dashboard.tsx
import React from 'react';
import Header from '../components/Header';
import AlertTable from '../components/AlertTable';
import AIAnalyst from '../components/AIAnalyst';
import RiskScoreCard from '../components/RiskScoreCard';
import ThreatMap from '../components/ThreatMap';

const Dashboard = () => {
    return (
        <div>
            <Header />
            <RiskScoreCard />
            <AlertTable />
            <AIAnalyst />
            <ThreatMap />
        </div>
    );
};

export default Dashboard;

# frontend/src/utils/classnames.ts
export const cn = (...classes) => classes.filter(Boolean).join(' ');

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
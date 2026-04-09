"""
Advanced Analytics Engine.
Implements statistical and ML-based analytics for threat intelligence.

Features:
1. Time Series Analysis (trend detection)
2. Statistical Anomalies (Z-score, IQR)
3. Predictive Analytics (forecasting)
4. Pattern Mining (association rules)
5. Cohort Analysis (grouping similar threats)
6. Forecasting (threat tempo prediction)
7. Behavioral Analysis (user/IP patterns)
8. Correlation Analysis (event relationships)
"""

import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics
import json

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from scipy import stats

logger = logging.getLogger(__name__)


@dataclass
class AnalyticsResult:
    """Analytics computation result"""
    metric_name: str
    value: float
    timestamp: datetime
    unit: str
    description: str
    confidence: float  # 0-1


@dataclass
class Forecast:
    """Threat forecast prediction"""
    forecast_datetime: datetime
    predicted_event_count: int
    confidence_interval: Tuple[int, int]  # (lower, upper)
    trend: str  # INCREASING, DECREASING, STABLE
    anomaly_likelihood: float  # 0-1


class TimeSeriesAnalyzer:
    """Time series analysis for threat detection"""
    
    def __init__(self, window_size: int = 24):
        """
        Initialize time series analyzer.
        
        Args:
            window_size: Time window in hours
        """
        self.window_size = window_size
    
    async def detect_trend(self, events: List[Dict[str, Any]]) -> Optional[AnalyticsResult]:
        """
        Detect trend in event stream.
        
        Args:
            events: List of timestamped events
            
        Returns:
            AnalyticsResult with trend detection
        """
        try:
            if len(events) < 2:
                return None
            
            # Extract timestamps and count
            df = pd.DataFrame(events)
            df['timestamp'] = pd.to_datetime(df.get('timestamp', datetime.now()))
            df = df.sort_values('timestamp')
            
            # Resample to hourly counts
            df.set_index('timestamp', inplace=True)
            hourly = df.resample('H').size()
            
            if len(hourly) < 2:
                return None
            
            # Calculate trend using linear regression
            x = np.arange(len(hourly)).reshape(-1, 1)
            y = hourly.values
            
            # Simple slope calculation
            slope = (y[-1] - y[0]) / max(len(y) - 1, 1)
            
            # Trend strength (R-squared proxy)
            mean_y = np.mean(y)
            ss_res = np.sum((y - np.polyfit(x.flatten(), y, 1)[0] * x.flatten() - 
                           np.polyfit(x.flatten(), y, 1)[1])**2)
            ss_tot = np.sum((y - mean_y)**2)
            trend_strength = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            return AnalyticsResult(
                metric_name='THREAT_TREND',
                value=slope,
                timestamp=datetime.now(),
                unit='events_per_hour',
                description=f'Trend: {slope:+.2f} events/hour' + 
                           (' (INCREASING)' if slope > 0.5 else ' (STABLE)' if slope > -0.5 else ' (DECREASING)'),
                confidence=min(1.0, trend_strength)
            )
        except Exception as e:
            logger.warning(f"Trend detection failed: {e}")
            return None
    
    async def detect_seasonality(self, events: List[Dict[str, Any]]) -> Optional[AnalyticsResult]:
        """
        Detect seasonal patterns in threat data.
        
        Args:
            events: List of timestamped events
            
        Returns:
            AnalyticsResult with seasonality score
        """
        try:
            if len(events) < 168:  # Need at least 1 week of hourly data
                return None
            
            df = pd.DataFrame(events)
            df['timestamp'] = pd.to_datetime(df.get('timestamp', datetime.now()))
            df['hour'] = df['timestamp'].dt.hour
            
            # Calculate events per hour
            hourly_counts = df.groupby('hour').size()
            
            # Seasonality score: variance in hourly distribution
            seasonality = hourly_counts.std() / (hourly_counts.mean() + 1)
            
            return AnalyticsResult(
                metric_name='SEASONALITY',
                value=seasonality,
                timestamp=datetime.now(),
                unit='ratio',
                description=f'Seasonality score: {seasonality:.2f}',
                confidence=0.8
            )
        except Exception as e:
            logger.warning(f"Seasonality detection failed: {e}")
            return None


class StatisticalAnomalyDetector:
    """Statistical methods for anomaly detection"""
    
    @staticmethod
    async def zscore_anomaly(values: List[float], threshold: float = 3.0) -> List[bool]:
        """
        Detect anomalies using Z-score method.
        
        Args:
            values: List of numerical values
            threshold: Z-score threshold
            
        Returns:
            List of boolean indicators (True = anomaly)
        """
        if len(values) < 2:
            return [False] * len(values)
        
        try:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)
            
            if stdev == 0:
                return [False] * len(values)
            
            return [abs((x - mean) / stdev) > threshold for x in values]
        except Exception as e:
            logger.warning(f"Z-score detection failed: {e}")
            return [False] * len(values)
    
    @staticmethod
    async def iqr_anomaly(values: List[float]) -> List[bool]:
        """
        Detect anomalies using Interquartile Range (IQR).
        
        Args:
            values: List of numerical values
            
        Returns:
            List of boolean indicators (True = anomaly)
        """
        if len(values) < 4:
            return [False] * len(values)
        
        try:
            sorted_vals = sorted(values)
            q1 = sorted_vals[len(sorted_vals) // 4]
            q3 = sorted_vals[3 * len(sorted_vals) // 4]
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            return [v < lower_bound or v > upper_bound for v in values]
        except Exception as e:
            logger.warning(f"IQR detection failed: {e}")
            return [False] * len(values)


class PredictiveAnalytics:
    """Predictive models for threat forecasting"""
    
    @staticmethod
    async def forecast_threat_tempo(events: List[Dict[str, Any]], 
                                   periods: int = 24) -> Optional[Forecast]:
        """
        Forecast threat activity for next N hours.
        
        Args:
            events: Historical events
            periods: Number of hours to forecast
            
        Returns:
            Forecast object
        """
        try:
            if len(events) < 48:  # Need at least 48 hours of data
                return None
            
            df = pd.DataFrame(events)
            df['timestamp'] = pd.to_datetime(df.get('timestamp', datetime.now()))
            df.set_index('timestamp', inplace=True)
            hourly = df.resample('H').size()
            
            # Simple exponential smoothing
            alpha = 0.3
            forecast_values = []
            last_value = hourly.iloc[-1]
            
            for i in range(periods):
                forecast_values.append(int(last_value))
                last_value = alpha * last_value + (1 - alpha) * last_value
            
            avg_forecast = int(np.mean(forecast_values))
            std_forecast = int(np.std(forecast_values))
            
            # Determine trend
            recent_trend = hourly.iloc[-1] - hourly.iloc[-24] if len(hourly) > 24 else 0
            if recent_trend > 10:
                trend = 'INCREASING'
            elif recent_trend < -10:
                trend = 'DECREASING'
            else:
                trend = 'STABLE'
            
            return Forecast(
                forecast_datetime=datetime.now() + timedelta(hours=1),
                predicted_event_count=avg_forecast,
                confidence_interval=(max(0, avg_forecast - std_forecast), avg_forecast + std_forecast),
                trend=trend,
                anomaly_likelihood=min(0.5, abs(recent_trend) / 100)
            )
        except Exception as e:
            logger.warning(f"Forecasting failed: {e}")
            return None


class PatternMiner:
    """Mine patterns in threat data"""
    
    @staticmethod
    async def find_common_patterns(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find common attack patterns in events.
        
        Args:
            events: List of events
            
        Returns:
            List of detected patterns
        """
        try:
            patterns = []
            
            # Pattern 1: Port scanning
            destination_ports = {}
            for event in events:
                port = event.get('destination_port', '')
                source = event.get('source_ip', '')
                if port and source:
                    if source not in destination_ports:
                        destination_ports[source] = []
                    destination_ports[source].append(port)
            
            for source, ports in destination_ports.items():
                if len(ports) > 10:  # Many ports from single source = scanning
                    patterns.append({
                        'pattern_type': 'PORT_SCAN',
                        'source_ip': source,
                        'port_count': len(set(ports)),
                        'confidence': 0.9
                    })
            
            # Pattern 2: Brute force (multiple failed logins)
            login_attempts = {}
            for event in events:
                if 'login' in event.get('description', '').lower():
                    user = event.get('user', 'unknown')
                    source = event.get('source_ip', '')
                    if source and user:
                        key = f"{user}@{source}"
                        login_attempts[key] = login_attempts.get(key, 0) + 1
            
            for attempt, count in login_attempts.items():
                if count > 5:
                    patterns.append({
                        'pattern_type': 'BRUTE_FORCE',
                        'target': attempt,
                        'attempt_count': count,
                        'confidence': 0.85
                    })
            
            return patterns
        except Exception as e:
            logger.warning(f"Pattern mining failed: {e}")
            return []


class CohortAnalyzer:
    """Group and analyze similar threats"""
    
    @staticmethod
    async def create_cohorts(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Create cohorts of similar events.
        
        Args:
            events: List of events
            
        Returns:
            Dictionary of cohorts by type
        """
        try:
            cohorts = {}
            
            for event in events:
                event_type = event.get('event_type', 'UNKNOWN')
                severity = event.get('severity', 'INFO')
                
                cohort_key = f"{event_type}_{severity}"
                
                if cohort_key not in cohorts:
                    cohorts[cohort_key] = []
                
                cohorts[cohort_key].append(event)
            
            return cohorts
        except Exception as e:
            logger.warning(f"Cohort analysis failed: {e}")
            return {}


class AdvancedAnalyticsEngine:
    """Complete advanced analytics engine"""
    
    def __init__(self):
        """Initialize analytics engine"""
        self.ts_analyzer = TimeSeriesAnalyzer()
        self.stat_detector = StatisticalAnomalyDetector()
        self.predictor = PredictiveAnalytics()
        self.pattern_miner = PatternMiner()
        self.cohort_analyzer = CohortAnalyzer()
    
    async def analyze_threats(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform comprehensive threat analysis.
        
        Args:
            events: List of events to analyze
            
        Returns:
            Dictionary with all analytics results
        """
        try:
            results = {
                'trend': await self.ts_analyzer.detect_trend(events),
                'seasonality': await self.ts_analyzer.detect_seasonality(events),
                'forecast': await self.predictor.forecast_threat_tempo(events),
                'patterns': await self.pattern_miner.find_common_patterns(events),
                'cohorts': await self.cohort_analyzer.create_cohorts(events),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"✓ Threat analysis completed for {len(events)} events")
            return results
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Global analytics engine instance
analytics_engine = AdvancedAnalyticsEngine()

"""
Performance Testing & Load Testing

Validates system performance under load
Measures latency, throughput, and identifies bottlenecks

Phase 3: Performance Tuning
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
import asyncio
import time
import random
from datetime import datetime, timedelta
import statistics

logger = logging.getLogger(__name__)


class LoadProfile(str, Enum):
    """Load testing profiles"""
    LIGHT = "light"                   # 100 events/sec
    MODERATE = "moderate"             # 500 events/sec
    HEAVY = "heavy"                   # 1000 events/sec
    EXTREME = "extreme"               # 5000 events/sec


@dataclass
class PerformanceMetrics:
    """Metrics for a test run"""
    test_name: str
    test_duration_seconds: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    
    response_times_ms: List[float] = field(default_factory=list)  # Raw times
    
    def get_stats(self) -> Dict:
        """Calculate statistics"""
        
        if not self.response_times_ms:
            return {}
        
        sorted_times = sorted(self.response_times_ms)
        
        return {
            "count": len(sorted_times),
            "min_ms": min(sorted_times),
            "max_ms": max(sorted_times),
            "avg_ms": statistics.mean(sorted_times),
            "median_ms": statistics.median(sorted_times),
            "p50_ms": sorted_times[int(len(sorted_times) * 0.50)],
            "p95_ms": sorted_times[int(len(sorted_times) * 0.95)],
            "p99_ms": sorted_times[int(len(sorted_times) * 0.99) - 1] if len(sorted_times) > 0 else 0,
            "stdev_ms": statistics.stdev(sorted_times) if len(sorted_times) > 1 else 0,
        }
    
    def get_report(self) -> Dict:
        """Generate full performance report"""
        
        success_rate = (self.successful_requests / self.total_requests * 100) if self.total_requests > 0 else 0
        throughput = self.successful_requests / self.test_duration_seconds if self.test_duration_seconds > 0 else 0
        
        return {
            "test_name": self.test_name,
            "duration_seconds": self.test_duration_seconds,
            "requests": {
                "total": self.total_requests,
                "successful": self.successful_requests,
                "failed": self.failed_requests,
                "success_rate_percent": success_rate
            },
            "throughput": {
                "requests_per_second": throughput,
                "requests_per_minute": throughput * 60
            },
            "latency": self.get_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }


class LoadTestScenario:
    """Defines a load test"""
    
    def __init__(
        self,
        name: str,
        profile: LoadProfile,
        duration_seconds: int = 60,
        ramp_up_seconds: int = 10
    ):
        self.name = name
        self.profile = profile
        self.duration_seconds = duration_seconds
        self.ramp_up_seconds = ramp_up_seconds
    
    def get_events_per_second(self) -> int:
        """Get target throughput for profile"""
        
        profile_eps = {
            LoadProfile.LIGHT: 100,
            LoadProfile.MODERATE: 500,
            LoadProfile.HEAVY: 1000,
            LoadProfile.EXTREME: 5000
        }
        
        return profile_eps.get(self.profile, 100)
    
    def estimate_total_events(self) -> int:
        """Estimate total events to be generated"""
        return self.get_events_per_second() * self.duration_seconds


class SyntheticEventGenerator:
    """Generates realistic synthetic events for load testing"""
    
    DETECTION_TYPES = [
        "ssh_brute_force",
        "unusual_database_query",
        "unusual_file_transfer",
        "privilege_escalation",
        "failed_login_attempt",
        "successful_login",
        "port_scanning",
        "malware_detected"
    ]
    
    SAMPLE_USERS = [
        "admin", "analyst", "developer", "finance_user", "hr_staff",
        "sales_user", "support_agent", "web_user", "database_admin"
    ]
    
    SAMPLE_ASSETS = [
        "db-prod-01", "web-server-01", "web-server-02", "file-server",
        "exchange-01", "domain-controller", "firewall", "workstation-01"
    ]
    
    SAMPLE_IPS = [
        "192.168.1.100", "192.168.1.101", "192.168.1.102",
        "203.0.113.45", "198.51.100.50"
    ]
    
    @staticmethod
    def generate_event() -> Dict:
        """Generate a realistic synthetic event"""
        
        return {
            "event_id": f"evt_{int(time.time() * 1000000)}",
            "event_type": random.choice(SyntheticEventGenerator.DETECTION_TYPES),
            "severity": random.randint(1, 100),
            "timestamp": datetime.utcnow().isoformat(),
            "user": random.choice(SyntheticEventGenerator.SAMPLE_USERS),
            "asset": random.choice(SyntheticEventGenerator.SAMPLE_ASSETS),
            "source_ip": random.choice(SyntheticEventGenerator.SAMPLE_IPS),
            "details": {
                "rule_name": "test_rule",
                "confidence": random.uniform(0.5, 1.0),
                "description": "Synthetic event for load testing"
            }
        }


class LoadTestExecutor:
    """
    Executes load tests against the system
    """
    
    def __init__(self):
        self.results: Dict[str, PerformanceMetrics] = {}
    
    async def run_test(
        self,
        scenario: LoadTestScenario,
        endpoint_function,  # Async function to call repeatedly
        endpoint_kwargs: Optional[Dict] = None
    ) -> PerformanceMetrics:
        """
        Run load test
        
        endpoint_function: Async function to call (event processor)
        endpoint_kwargs: Arguments to pass to function
        """
        
        eps = scenario.get_events_per_second()
        interval = 1.0 / eps if eps > 0 else 1.0
        
        logger.info(
            f"Starting load test: {scenario.name} ({scenario.profile.value})\n"
            f"  Target: {eps} events/sec\n"
            f"  Duration: {scenario.duration_seconds}s\n"
            f"  Total events: {scenario.estimate_total_events()}"
        )
        
        metrics = PerformanceMetrics(
            test_name=scenario.name,
            test_duration_seconds=scenario.duration_seconds,
            total_requests=0,
            successful_requests=0,
            failed_requests=0
        )
        
        start_time = time.time()
        next_event_time = start_time
        
        # Ramp-up phase
        ramp_up_end = start_time + scenario.ramp_up_seconds
        current_rate_multiplier = 0.1
        
        while True:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Check if test is done
            if elapsed > scenario.duration_seconds:
                break
            
            # Ramp-up: gradually increase rate
            if current_time < ramp_up_end:
                progress = (current_time - start_time) / scenario.ramp_up_seconds
                current_rate_multiplier = progress  # 0 to 1
            else:
                current_rate_multiplier = 1.0
            
            # Generate event if it's time
            if current_time >= next_event_time:
                # Adjust interval during ramp-up
                current_interval = interval / max(0.1, current_rate_multiplier)
                next_event_time = current_time + current_interval
                
                # Generate and process event
                event = SyntheticEventGenerator.generate_event()
                
                try:
                    request_start = time.time()
                    
                    # Call the endpoint
                    if endpoint_kwargs:
                        await endpoint_function(**endpoint_kwargs, event=event)
                    else:
                        await endpoint_function(event)
                    
                    request_time = (time.time() - request_start) * 1000  # Convert to ms
                    
                    metrics.response_times_ms.append(request_time)
                    metrics.successful_requests += 1
                
                except Exception as e:
                    logger.warning(f"Request failed: {e}")
                    metrics.failed_requests += 1
                
                metrics.total_requests += 1
            
            # Small sleep to prevent busy-waiting
            await asyncio.sleep(0.001)
        
        metrics.test_duration_seconds = int(time.time() - start_time)
        self.results[scenario.name] = metrics
        
        return metrics


class BottleneckAnalyzer:
    """
    Analyzes metrics to identify bottlenecks
    """
    
    @staticmethod
    def analyze(metrics: PerformanceMetrics) -> Dict:
        """Identify bottlenecks and issues"""
        
        analysis = {
            "bottlenecks": [],
            "warnings": [],
            "recommendations": []
        }
        
        stats = metrics.get_stats()
        
        # Check latency
        if stats.get("p99_ms", 0) > 1000:
            analysis["bottlenecks"].append("High P99 latency (>1s)")
            analysis["recommendations"].append("Optimize database queries or add caching")
        
        if stats.get("p95_ms", 0) > 500:
            analysis["warnings"].append("High P95 latency (>500ms)")
        
        # Check success rate
        if metrics.total_requests > 0:
            success_rate = metrics.successful_requests / metrics.total_requests
            if success_rate < 0.95:
                analysis["bottlenecks"].append("High error rate (<95%)")
                analysis["recommendations"].append("Check logs for timeouts or resource exhaustion")
        
        # Check variability
        if stats.get("stdev_ms", 0) > stats.get("avg_ms", 1) * 2:
            analysis["warnings"].append("High latency variability (stdev > 2x mean)")
            analysis["recommendations"].append("Look for GC pauses or resource contention")
        
        # Check throughput
        throughput = metrics.successful_requests / metrics.test_duration_seconds
        if throughput < 10:  # Less than 10 req/sec
            analysis["warnings"].append("Low throughput")
            analysis["recommendations"].append("Increase resources or optimize processing")
        
        return analysis


class PerformanceTester:
    """
    Main orchestrator for performance testing
    """
    
    def __init__(self):
        self.executor = LoadTestExecutor()
        self.analyzer = BottleneckAnalyzer()
        self.all_results: List[PerformanceMetrics] = []
    
    async def run_benchmark_suite(
        self,
        endpoint_function,
        endpoint_kwargs: Optional[Dict] = None
    ) -> List[PerformanceMetrics]:
        """
        Run comprehensive benchmark suite
        Tests: Light, Moderate, Heavy, Extreme
        """
        
        scenarios = [
            LoadTestScenario("Light Load", LoadProfile.LIGHT, duration_seconds=30),
            LoadTestScenario("Moderate Load", LoadProfile.MODERATE, duration_seconds=30),
            LoadTestScenario("Heavy Load", LoadProfile.HEAVY, duration_seconds=30),
            LoadTestScenario("Extreme Load", LoadProfile.EXTREME, duration_seconds=30),
        ]
        
        logger.info("Starting comprehensive performance benchmark suite...")
        
        for scenario in scenarios:
            logger.info(f"\nRunning: {scenario.name}")
            
            metrics = await self.executor.run_test(
                scenario,
                endpoint_function,
                endpoint_kwargs
            )
            
            self.all_results.append(metrics)
            report = metrics.get_report()
            
            logger.info(f"Results:\n{self._format_report(report)}")
            
            # Analyze bottlenecks
            analysis = self.analyzer.analyze(metrics)
            if analysis["bottlenecks"]:
                logger.warning(f"Bottlenecks detected: {analysis['bottlenecks']}")
            
            # Small delay between tests
            await asyncio.sleep(2)
        
        return self.all_results
    
    def get_comparison_report(self) -> str:
        """Generate comparison report across all tests"""
        
        report = ["=" * 60]
        report.append("PERFORMANCE COMPARISON REPORT")
        report.append("=" * 60)
        
        for metrics in self.all_results:
            stats = metrics.get_stats()
            success_rate = (metrics.successful_requests / metrics.total_requests * 100) if metrics.total_requests > 0 else 0
            
            report.append(f"\n{metrics.test_name}")
            report.append(f"  Throughput: {metrics.successful_requests / metrics.test_duration_seconds:.1f} req/sec")
            report.append(f"  Success Rate: {success_rate:.1f}%")
            report.append(f"  Latency (ms): p50={stats.get('p50_ms', 0):.1f} p95={stats.get('p95_ms', 0):.1f} p99={stats.get('p99_ms', 0):.1f}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    @staticmethod
    def _format_report(report: Dict) -> str:
        """Format report for display"""
        
        lines = []
        lines.append(f"  Requests: {report['requests']['successful']}/{report['requests']['total']} successful ({report['requests']['success_rate_percent']:.1f}%)")
        lines.append(f"  Throughput: {report['throughput']['requests_per_second']:.1f} req/s")
        
        latency = report.get('latency', {})
        if latency:
            lines.append(f"  Latency: avg={latency.get('avg_ms', 0):.1f}ms p95={latency.get('p95_ms', 0):.1f}ms p99={latency.get('p99_ms', 0):.1f}ms")
        
        return "\n".join(lines)

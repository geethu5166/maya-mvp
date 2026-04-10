"""
Module Watchdog Service - Monitoring & Auto-Restart for All Services
Ensures honeypots, workers, and critical services stay alive
"""

import asyncio
import logging
import threading
from typing import Dict, Callable, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import subprocess

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service status"""
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    STOPPED = "STOPPED"
    RESTARTING = "RESTARTING"


@dataclass
class ServiceInfo:
    """Service monitoring information"""
    name: str
    service_func: Callable
    is_async: bool
    status: ServiceStatus = ServiceStatus.STOPPED
    thread: Optional[threading.Thread] = None
    last_check: Optional[datetime] = None
    restart_count: int = 0
    failure_count: int = 0
    last_error: Optional[str] = None


class ModuleWatchdog:
    """
    Monitors critical services and auto-restarts failed ones
    
    Features:
    - Health checking for all registered services
    - Auto-restart on failure
    - Restart backoff (1s, 5s, 30s)
    - Logging of all failures
    - Dashboard stats
    """
    
    def __init__(self, check_interval_seconds: int = 30, max_retries: int = 3):
        """
        Initialize watchdog
        
        Args:
            check_interval_seconds: How often to check service health
            max_retries: Max restart attempts before giving up
        """
        self.services: Dict[str, ServiceInfo] = {}
        self.check_interval = check_interval_seconds
        self.max_retries = max_retries
        self.is_running = False
        self.watchdog_thread: Optional[threading.Thread] = None
        self.restart_backoff = {0: 1, 1: 5, 2: 30}  # seconds
    
    def register_service(
        self,
        name: str,
        service_func: Callable,
        is_async: bool = False
    ) -> None:
        """
        Register a service to monitor
        
        Args:
            name: Service name (e.g., 'ssh_honeypot')
            service_func: Async or sync function that runs the service
            is_async: True if service_func is async
        """
        self.services[name] = ServiceInfo(
            name=name,
            service_func=service_func,
            is_async=is_async
        )
        logger.info(f"✓ Registered service for monitoring: {name}")
    
    def _run_sync_service(self, service: ServiceInfo) -> None:
        """Run synchronous service in thread"""
        try:
            service.status = ServiceStatus.RUNNING
            logger.info(f"▶ Starting service: {service.name}")
            service.service_func()
        except Exception as e:
            service.status = ServiceStatus.FAILED
            service.failure_count += 1
            service.last_error = str(e)
            logger.error(f"✗ Service {service.name} failed: {e}")
    
    def _run_async_service(self, service: ServiceInfo) -> None:
        """Run async service by creating new event loop"""
        try:
            service.status = ServiceStatus.RUNNING
            logger.info(f"▶ Starting async service: {service.name}")
            asyncio.run(service.service_func())
        except Exception as e:
            service.status = ServiceStatus.FAILED
            service.failure_count += 1
            service.last_error = str(e)
            logger.error(f"✗ Async service {service.name} failed: {e}")
    
    def start_service(self, service: ServiceInfo) -> bool:
        """
        Start a service in a background thread
        
        Returns:
            True if service started successfully
        """
        try:
            if service.thread and service.thread.is_alive():
                logger.warning(f"Service {service.name} already running")
                return True
            
            # Create thread
            if service.is_async:
                service.thread = threading.Thread(
                    target=self._run_async_service,
                    args=(service,),
                    daemon=True,
                    name=f"thread-{service.name}"
                )
            else:
                service.thread = threading.Thread(
                    target=self._run_sync_service,
                    args=(service,),
                    daemon=True,
                    name=f"thread-{service.name}"
                )
            
            # Start thread
            service.thread.start()
            service.status = ServiceStatus.STARTING
            logger.info(f"✓ Service thread started: {service.name}")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed to start service {service.name}: {e}")
            return False
    
    def check_service_health(self, service: ServiceInfo) -> bool:
        """
        Check if service is still running
        
        Returns:
            True if healthy, False if failed
        """
        service.last_check = datetime.now()
        
        # Check if thread is alive
        if service.thread and service.thread.is_alive():
            service.status = ServiceStatus.RUNNING
            service.failure_count = 0  # Reset failures
            return True
        else:
            # Thread dead or never started
            if service.status == ServiceStatus.RUNNING:
                logger.warning(f"⚠ Service {service.name} died unexpectedly")
            service.status = ServiceStatus.FAILED
            return False
    
    def _auto_restart_service(self, service: ServiceInfo) -> None:
        """
        Auto-restart failed service with backoff
        """
        if service.failure_count >= self.max_retries:
            logger.critical(
                f"✗ Service {service.name} failed {self.max_retries} times, "
                f"giving up. Last error: {service.last_error}"
            )
            return
        
        # Wait before restart (backoff)
        backoff_seconds = self.restart_backoff.get(service.restart_count, 60)
        logger.info(f"⏳ Restarting {service.name} in {backoff_seconds}s...")
        
        import time
        time.sleep(backoff_seconds)
        
        service.restart_count += 1
        service.status = ServiceStatus.RESTARTING
        self.start_service(service)
    
    def _watchdog_loop(self) -> None:
        """Background watchdog thread loop"""
        logger.info("🐕 Watchdog monitoring started")
        
        while self.is_running:
            try:
                for service_name, service in self.services.items():
                    # Check health
                    is_healthy = self.check_service_health(service)
                    
                    if not is_healthy and service.status == ServiceStatus.FAILED:
                        # Auto-restart
                        logger.warning(f"🔄 Auto-restarting failed service: {service_name}")
                        self._auto_restart_service(service)
                
                # Wait before next check
                import time
                time.sleep(self.check_interval)
            
            except Exception as e:
                logger.error(f"Watchdog error: {e}")
                import time
                time.sleep(5)
    
    def start(self) -> bool:
        """Start watchdog and all registered services"""
        try:
            logger.info(f"🚀 Starting watchdog with {len(self.services)} services")
            
            # Start all services
            for service in self.services.values():
                self.start_service(service)
            
            # Start watchdog thread
            self.is_running = True
            self.watchdog_thread = threading.Thread(
                target=self._watchdog_loop,
                daemon=True,
                name="watchdog-thread"
            )
            self.watchdog_thread.start()
            
            logger.info("✓ Watchdog started successfully")
            return True
        
        except Exception as e:
            logger.error(f"✗ Failed to start watchdog: {e}")
            return False
    
    def stop(self) -> None:
        """Stop watchdog and all services"""
        try:
            logger.info("Stopping watchdog...")
            self.is_running = False
            
            # Wait for watchdog thread to finish
            if self.watchdog_thread and self.watchdog_thread.is_alive():
                self.watchdog_thread.join(timeout=5)
            
            logger.info("✓ Watchdog stopped")
        except Exception as e:
            logger.error(f"Error stopping watchdog: {e}")
    
    def get_status(self) -> Dict:
        """Get status of all monitored services"""
        return {
            "watchdog_running": self.is_running,
            "services": {
                name: {
                    "status": service.status.value,
                    "restart_count": service.restart_count,
                    "failure_count": service.failure_count,
                    "last_check": service.last_check.isoformat() if service.last_check else None,
                    "last_error": service.last_error,
                }
                for name, service in self.services.items()
            }
        }
    
    def get_service_status(self, service_name: str) -> Optional[Dict]:
        """Get status of specific service"""
        if service_name not in self.services:
            return None
        
        service = self.services[service_name]
        return {
            "name": service.name,
            "status": service.status.value,
            "is_alive": service.thread.is_alive() if service.thread else False,
            "restart_count": service.restart_count,
            "failure_count": service.failure_count,
            "last_error": service.last_error,
        }


# Global watchdog instance
watchdog: Optional[ModuleWatchdog] = None


def get_watchdog() -> ModuleWatchdog:
    """Get global watchdog instance"""
    global watchdog
    if watchdog is None:
        watchdog = ModuleWatchdog()
    return watchdog


# Example usage in main.py:
# 
# from app.core.watchdog import get_watchdog
# 
# async def main():
#     wd = get_watchdog()
#     
#     # Register honeypots
#     wd.register_service("ssh_honeypot", start_ssh_honeypot, is_async=False)
#     wd.register_service("web_honeypot", start_web_honeypot, is_async=False)
#     wd.register_service("db_honeypot", start_db_honeypot, is_async=False)  
#     
#     # Start watchdog
#     wd.start()
#     
#     # Watchdog will monitor and auto-restart all services
#     # Get status anytime: wd.get_status()

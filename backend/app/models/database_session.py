"""
DATABASE SESSION MANAGEMENT & INITIALIZATION
=============================================

SQLAlchemy session factory and database operations for MAYA SOC Enterprise.

Features:
- Connection pooling
- Session lifecycle management
- Multi-tenancy support
- Database initialization
- Migration management

Author: MAYA SOC Enterprise
Version: 1.0
"""

import logging
from sqlalchemy import create_engine, event, inspect, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool
from contextlib import contextmanager
from typing import Optional, Generator

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ==========================================
# DATABASE ENGINE & SESSION FACTORY
# ==========================================

class DatabaseManager:
    """
    Manages database connections, pooling, and session lifecycle
    
    Features:
    - Connection pooling (QueuePool for production)
    - Statement monitoring
    - Connection retry logic
    - Multi-tenancy isolation
    """
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self, database_url: Optional[str] = None) -> None:
        """
        Initialize database engine and session factory
        
        Args:
            database_url: PostgreSQL connection string
                         Default: From settings.POSTGRES_*
        """
        
        if self._initialized:
            logger.warning("Database already initialized")
            return
        
        # Build connection string from settings if not provided
        if not database_url:
            database_url = (
                f"postgresql+psycopg2://"
                f"{settings.POSTGRES_USER}:"
                f"{settings.POSTGRES_PASSWORD}@"
                f"{settings.POSTGRES_HOST}:"
                f"{settings.POSTGRES_PORT}/"
                f"{settings.POSTGRES_DB}"
            )
        
        logger.info(f"Connecting to database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
        
        # Create engine with connection pooling
        self.engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=20,  # Number of connections to keep
            max_overflow=40,  # Maximum overflow before blocking
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Verify connections before using
            echo=settings.DEBUG,  # Log SQL statements in debug mode
            connect_args={
                "connect_timeout": 10,
                "options": "-c statement_timeout=30000",  # 30 second statement timeout
            }
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Register event listeners
        self._register_event_listeners()
        
        self._initialized = True
        logger.info("✓ Database initialized and ready")
    
    def _register_event_listeners(self) -> None:
        """Register SQLAlchemy event listeners for monitoring"""
        
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Log successful connections"""
            logger.debug("Database connection established")
        
        @event.listens_for(self.engine, "close")
        def receive_close(dbapi_conn, connection_record):
            """Log connection closure"""
            logger.debug("Database connection closed")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_conn, connection_record):
            """Log connection return to pool"""
            logger.debug("Connection returned to pool")
    
    def get_session(self) -> Session:
        """Get a new database session"""
        if not self._initialized:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Context manager for session lifecycle
        
        Usage:
            with db_manager.session_scope() as session:
                user = session.query(User).first()
        
        Automatically commits on success, rolls back on exception
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            session.close()
    
    def health_check(self) -> tuple[bool, str]:
        """
        Check database connectivity and health
        
        Returns:
            (is_healthy, message)
        """
        if not self._initialized or not self.engine:
            return False, "Database not initialized"
        
        try:
            with self.engine.connect() as conn:
                result = conn.execute("SELECT 1")
                if result:
                    return True, "Database healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False, f"Database unhealthy: {str(e)}"
        
        return False, "Unknown database error"
    
    def create_tables(self) -> None:
        """Create all database tables"""
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        
        try:
            from app.models.database import Base
            
            logger.info("Creating database tables...")
            Base.metadata.create_all(self.engine)
            logger.info("✓ All database tables created")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self) -> None:
        """Drop all database tables (use with caution)"""
        if not self._initialized:
            raise RuntimeError("Database not initialized")
        
        try:
            from app.models.database import Base
            
            logger.warning("Dropping all database tables...")
            Base.metadata.drop_all(self.engine)
            logger.info("✓ All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    def get_table_info(self) -> dict:
        """Get information about all tables"""
        if not self._initialized or not self.engine:
            return {}
        
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        
        table_info = {}
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            table_info[table_name] = {
                'column_count': len(columns),
                'columns': [col['name'] for col in columns]
            }
        
        return table_info


# ==========================================
# GLOBAL DATABASE MANAGER INSTANCE
# ==========================================

database = DatabaseManager()


async def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session
    
    Usage in endpoints:
        @app.get("/incidents")
        async def get_incidents(session: Session = Depends(get_db_session)):
            incidents = session.query(Incident).all()
            return incidents
    """
    session = database.get_session()
    try:
        yield session
    finally:
        session.close()


# ==========================================
# DATABASE QUERIES - HELPER FUNCTIONS
# ==========================================

class EventQueries:
    """Helper queries for Event model"""
    
    @staticmethod
    def get_recent_events(session: Session, tenant_id: str, limit: int = 100):
        """Get recent events for a tenant"""
        from app.models.database import Event
        
        return (
            session.query(Event)
            .filter(Event.tenant_id == tenant_id)
            .order_by(Event.timestamp.desc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def get_events_by_severity(session: Session, tenant_id: str, severity):
        """Get events filtered by severity"""
        from app.models.database import Event
        
        return (
            session.query(Event)
            .filter(
                Event.tenant_id == tenant_id,
                Event.severity == severity
            )
            .order_by(Event.timestamp.desc())
            .all()
        )
    
    @staticmethod
    def count_events_by_severity(session: Session, tenant_id: str) -> dict:
        """Count events by severity"""
        from app.models.database import Event, EventSeverity
        
        counts = {}
        for severity in EventSeverity:
            count = (
                session.query(Event)
                .filter(
                    Event.tenant_id == tenant_id,
                    Event.severity == severity
                )
                .count()
            )
            counts[severity.value] = count
        
        return counts


class IncidentQueries:
    """Helper queries for Incident model"""
    
    @staticmethod
    def get_open_incidents(session: Session, tenant_id: str):
        """Get all open incidents"""
        from app.models.database import Incident, IncidentStatus
        
        return (
            session.query(Incident)
            .filter(
                Incident.tenant_id == tenant_id,
                Incident.status == IncidentStatus.OPEN
            )
            .order_by(Incident.created_at.desc())
            .all()
        )
    
    @staticmethod
    def get_incidents_by_priority(session: Session, tenant_id: str, priority):
        """Get incidents by priority"""
        from app.models.database import Incident
        
        return (
            session.query(Incident)
            .filter(
                Incident.tenant_id == tenant_id,
                Incident.priority == priority
            )
            .order_by(Incident.created_at.desc())
            .all()
        )
    
    @staticmethod
    def get_unassigned_incidents(session: Session, tenant_id: str):
        """Get incidents not yet assigned"""
        from app.models.database import Incident
        
        return (
            session.query(Incident)
            .filter(
                Incident.tenant_id == tenant_id,
                Incident.assigned_analyst_id.is_(None)
            )
            .order_by(Incident.priority.desc())
            .all()
        )
    
    @staticmethod
    def get_incident_with_events(session: Session, incident_id: str):
        """Get incident with all related events"""
        from app.models.database import Incident
        
        return (
            session.query(Incident)
            .filter(Incident.incident_id == incident_id)
            .first()
        )


class HoneypotQueries:
    """Helper queries for honeypot interactions"""
    
    @staticmethod
    def get_recent_intrusions(session: Session, tenant_id: str, limit: int = 50):
        """Get recent honeypot interactions"""
        from app.models.database import HoneypotInteraction
        
        return (
            session.query(HoneypotInteraction)
            .filter(HoneypotInteraction.tenant_id == tenant_id)
            .order_by(HoneypotInteraction.timestamp.desc())
            .limit(limit)
            .all()
        )
    
    @staticmethod
    def get_active_attackers(session: Session, tenant_id: str):
        """Get list of active attacker IPs"""
        from app.models.database import HoneypotInteraction
        
        return (
            session.query(HoneypotInteraction.source_ip, 
                         func.count(HoneypotInteraction.interaction_id).label('count'))
            .filter(HoneypotInteraction.tenant_id == tenant_id)
            .group_by(HoneypotInteraction.source_ip)
            .order_by('count'.desc())
            .all()
        )


# ==========================================
# INITIALIZATION FUNCTION
# ==========================================

async def init_database() -> bool:
    """
    Initialize database on application startup
    
    Should be called in app.main.lifespan()
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize connection manager
        database.initialize()
        
        # Create tables
        database.create_tables()
        
        # Verify health
        is_healthy, message = database.health_check()
        if is_healthy:
            logger.info("✓ Database initialization successful")
            return True
        else:
            logger.error(f"✗ Database health check failed: {message}")
            return False
    
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return False

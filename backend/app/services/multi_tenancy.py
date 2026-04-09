"""
Multi-Tenancy Support

Enables multiple customer isolation and per-tenant data management

Phase 3: Multi-Tenancy
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime
import contextvars

logger = logging.getLogger(__name__)


class TenantRole(str, Enum):
    """Roles for tenant users"""
    ADMIN = "admin"                    # All permissions
    SECURITY_ANALYST = "analyst"       # View, investigate
    SOC_MANAGER = "manager"            # View, respond, config
    VIEWER = "viewer"                  # Read-only


class PlanType(str, Enum):
    """Subscription plan types"""
    STARTER = "starter"                # 1 analyst, 100 events/day
    PROFESSIONAL = "professional"      # 5 analysts, 1000 events/day
    ENTERPRISE = "enterprise"          # Unlimited


@dataclass
class TenantUsageMetrics:
    """Track tenant resource usage"""
    events_processed_today: int = 0
    events_processed_monthly: int = 0
    users: int = 0
    notifications_sent: int = 0
    detections_created: int = 0


@dataclass
class Tenant:
    """Customer tenant configuration"""
    tenant_id: str
    name: str
    domain: str                        # customer.example.com
    plan: PlanType
    created_at: datetime
    is_active: bool = True
    has_api_access: bool = False
    api_keys: List[str] = field(default_factory=list)
    usage: TenantUsageMetrics = field(default_factory=TenantUsageMetrics)
    
    # Configuration
    retention_days: int = 90           # How long to keep data
    notification_channels: List[str] = field(default_factory=list)  # Email, Slack, etc.
    webhook_urls: List[str] = field(default_factory=list)
    
    # Customization
    custom_detection_rules: Dict = field(default_factory=dict)
    playbooks: Dict = field(default_factory=dict)
    
    def get_plan_limits(self) -> Dict:
        """Get quota limits for tenant plan"""
        
        limits = {
            "starter": {
                "max_users": 1,
                "max_events_per_day": 100,
                "max_api_calls_per_month": 1000,
                "data_retention_days": 30
            },
            "professional": {
                "max_users": 5,
                "max_events_per_day": 1000,
                "max_api_calls_per_month": 10000,
                "data_retention_days": 90
            },
            "enterprise": {
                "max_users": 999,
                "max_events_per_day": 999999,
                "max_api_calls_per_month": 999999,
                "data_retention_days": 365
            }
        }
        
        return limits[self.plan.value]
    
    def is_quota_exceeded(self, quota_type: str) -> bool:
        """Check if tenant has exceeded quota"""
        
        limits = self.get_plan_limits()
        
        if quota_type == "daily_events":
            return self.usage.events_processed_today >= limits["max_events_per_day"]
        elif quota_type == "monthly_users":
            return self.usage.users >= limits["max_users"]
        
        return False


@dataclass
class TenantUser:
    """User within a tenant"""
    user_id: str
    tenant_id: str
    username: str
    email: str
    role: TenantRole
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    mfa_enabled: bool = False
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has permission"""
        
        roles_permissions = {
            TenantRole.ADMIN: ["read", "write", "delete", "config", "users", "analytics"],
            TenantRole.SECURITY_ANALYST: ["read", "write", "analytics"],
            TenantRole.SOC_MANAGER: ["read", "write", "config", "analytics"],
            TenantRole.VIEWER: ["read", "analytics"]
        }
        
        return permission in roles_permissions.get(self.role, [])


# Context variable for tenant isolation
current_tenant: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'current_tenant',
    default=None
)

current_user: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    'current_user',
    default=None
)


class TenantManager:
    """Manages tenant operations"""
    
    def __init__(self):
        self.tenants: Dict[str, Tenant] = {}
        self.users: Dict[str, TenantUser] = {}
        self.api_key_to_tenant: Dict[str, str] = {}
    
    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        domain: str,
        plan: PlanType = PlanType.PROFESSIONAL
    ) -> Tenant:
        """Create new tenant"""
        
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            domain=domain,
            plan=plan,
            created_at=datetime.utcnow()
        )
        
        self.tenants[tenant_id] = tenant
        logger.info(f"Created tenant {tenant_id} ({name}) on {plan.value} plan")
        
        return tenant
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Retrieve tenant by ID"""
        return self.tenants.get(tenant_id)
    
    def list_tenants(self) -> List[Tenant]:
        """List all active tenants"""
        return [t for t in self.tenants.values() if t.is_active]
    
    def add_user_to_tenant(
        self,
        tenant_id: str,
        user_id: str,
        username: str,
        email: str,
        role: TenantRole
    ) -> Optional[TenantUser]:
        """Add user to tenant"""
        
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            logger.error(f"Tenant {tenant_id} not found")
            return None
        
        # Check user quota
        plan_limits = tenant.get_plan_limits()
        if tenant.usage.users >= plan_limits["max_users"]:
            logger.warning(f"Tenant {tenant_id} has reached user limit")
            return None
        
        user = TenantUser(
            user_id=user_id,
            tenant_id=tenant_id,
            username=username,
            email=email,
            role=role,
            created_at=datetime.utcnow()
        )
        
        self.users[user_id] = user
        tenant.usage.users += 1
        
        logger.info(f"Added user {username} to tenant {tenant_id} as {role.value}")
        
        return user
    
    def get_tenant_user(self, tenant_id: str, user_id: str) -> Optional[TenantUser]:
        """Get user within tenant"""
        
        user = self.users.get(user_id)
        if user and user.tenant_id == tenant_id:
            return user
        return None
    
    def authenticate_api_key(self, api_key: str) -> Optional[str]:
        """Validate API key and return tenant ID"""
        return self.api_key_to_tenant.get(api_key)
    
    def create_api_key(self, tenant_id: str) -> str:
        """Generate API key for tenant"""
        
        import secrets
        api_key = f"maya_{secrets.token_urlsafe(32)}"
        
        tenant = self.get_tenant(tenant_id)
        if tenant:
            tenant.api_keys.append(api_key)
            self.api_key_to_tenant[api_key] = tenant_id
            tenant.has_api_access = True
            logger.info(f"Created API key for tenant {tenant_id}")
        
        return api_key
    
    def get_tenant_stats(self, tenant_id: str) -> Dict:
        """Get usage statistics for tenant"""
        
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return {}
        
        plan_limits = tenant.get_plan_limits()
        
        return {
            "tenant_id": tenant_id,
            "name": tenant.name,
            "plan": tenant.plan.value,
            "created_at": tenant.created_at.isoformat(),
            "usage": {
                "events_today": tenant.usage.events_processed_today,
                "events_monthly": tenant.usage.events_processed_monthly,
                "users": tenant.usage.users,
                "notifications": tenant.usage.notifications_sent
            },
            "limits": plan_limits,
            "utilization": {
                "users_percent": (tenant.usage.users / plan_limits["max_users"]) * 100,
                "daily_events_percent": (tenant.usage.events_processed_today / plan_limits["max_events_per_day"]) * 100
            }
        }


class TenantQueryBuilder:
    """Builds database queries with automatic tenant filtering"""
    
    @staticmethod
    def filter_incidents(base_query, tenant_id: str):
        """Filter incidents by tenant"""
        return base_query.filter(Incident.tenant_id == tenant_id)
    
    @staticmethod
    def filter_detections(base_query, tenant_id: str):
        """Filter detections by tenant"""
        return base_query.filter(Detection.tenant_id == tenant_id)
    
    @staticmethod
    def filter_events(base_query, tenant_id: str):
        """Filter events by tenant"""
        return base_query.filter(Event.tenant_id == tenant_id)
    
    @staticmethod
    def filter_assets(base_query, tenant_id: str):
        """Filter assets by tenant"""
        return base_query.filter(Asset.tenant_id == tenant_id)


class TenantIsolationMiddleware:
    """
    Middleware to enforce tenant isolation
    
    Should be applied to all API endpoints
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_tenant_from_request(
        self,
        auth_token: Optional[str] = None,
        api_key: Optional[str] = None,
        host: Optional[str] = None
    ) -> Optional[str]:
        """
        Extract tenant ID from request
        
        Priority:
        1. API key in header
        2. Subdomain (customer.example.com)
        3. Auth token claims
        """
        
        # Check API key
        if api_key:
            tenant_id = current_tenant.get()
            if tenant_id:
                return tenant_id
        
        # Check subdomain-based routing
        if host:
            parts = host.split(".")
            if len(parts) > 2:  # tenant.example.com
                return parts[0]
        
        # Check JWT claims
        if auth_token:
            # In production: decode JWT and extract tenant_id from claims
            pass
        
        return None
    
    def set_current_tenant(self, tenant_id: str):
        """Set current tenant context"""
        current_tenant.set(tenant_id)
    
    def get_current_tenant(self) -> Optional[str]:
        """Get current tenant context"""
        return current_tenant.get()
    
    def enforce_tenant_isolation(
        self,
        requested_tenant_id: str,
        authenticated_tenant_id: str
    ) -> bool:
        """Verify that authenticated user can access requested tenant"""
        
        allowed = requested_tenant_id == authenticated_tenant_id
        
        if not allowed:
            self.logger.warning(
                f"Tenant isolation violation: User from {authenticated_tenant_id} "
                f"tried to access {requested_tenant_id}"
            )
        
        return allowed


class TenantDataMigration:
    """
    Helper for migrating existing single-tenant data to multi-tenant
    """
    
    @staticmethod
    def migrate_to_tenant(
        default_tenant_id: str,
        models_to_migrate: List[str]
    ) -> Dict[str, int]:
        """
        Add tenant_id to existing records
        
        models_to_migrate: ["Incident", "Detection", "Event", etc.]
        """
        
        results = {
            "migrated": 0,
            "failed": 0,
            "skipped": 0
        }
        
        # In production: Execute actual migration SQL
        # This is pseudocode showing the pattern
        
        for model_name in models_to_migrate:
            try:
                # Query all records without tenant_id
                # UPDATE model SET tenant_id = default_tenant_id WHERE tenant_id IS NULL
                
                results["migrated"] += 1
                logger.info(f"Migrated {model_name} to tenant {default_tenant_id}")
            
            except Exception as e:
                results["failed"] += 1
                logger.error(f"Failed to migrate {model_name}: {e}")
        
        return results


class PerTenantConfiguration:
    """
    Store and retrieve tenant-specific configurations
    """
    
    def __init__(self):
        self.configs: Dict[str, Dict] = {}
    
    def set_detection_rules(self, tenant_id: str, rules: List[Dict]):
        """Store custom detection rules for tenant"""
        if tenant_id not in self.configs:
            self.configs[tenant_id] = {}
        self.configs[tenant_id]["detection_rules"] = rules
        logger.info(f"Updated {len(rules)} detection rules for tenant {tenant_id}")
    
    def get_detection_rules(self, tenant_id: str) -> List[Dict]:
        """Retrieve detection rules for tenant"""
        if tenant_id not in self.configs:
            return []
        return self.configs[tenant_id].get("detection_rules", [])
    
    def set_playbooks(self, tenant_id: str, playbooks: List[Dict]):
        """Store automated playbooks for tenant"""
        if tenant_id not in self.configs:
            self.configs[tenant_id] = {}
        self.configs[tenant_id]["playbooks"] = playbooks
        logger.info(f"Updated {len(playbooks)} playbooks for tenant {tenant_id}")
    
    def get_playbooks(self, tenant_id: str) -> List[Dict]:
        """Retrieve playbooks for tenant"""
        if tenant_id not in self.configs:
            return []
        return self.configs[tenant_id].get("playbooks", [])
    
    def set_notification_settings(self, tenant_id: str, settings: Dict):
        """Store notification preferences for tenant"""
        if tenant_id not in self.configs:
            self.configs[tenant_id] = {}
        self.configs[tenant_id]["notifications"] = settings
        logger.info(f"Updated notification settings for tenant {tenant_id}")
    
    def get_notification_settings(self, tenant_id: str) -> Dict:
        """Retrieve notification settings for tenant"""
        if tenant_id not in self.configs:
            return {}
        return self.configs[tenant_id].get("notifications", {})

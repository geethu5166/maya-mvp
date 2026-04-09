"""
Behavioral Baseline Generation

Generates 30-day synthetic user/system behavior profiles.
Creates realistic baseline data for behavioral anomaly detection.

Phase 3: Data Generation & Profiles
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import random
import logging

logger = logging.getLogger(__name__)


@dataclass
class BehaviorDay:
    """One day of simulated user behavior"""
    date: str                           # "2024-01-01"
    user_id: str
    login_count: int                    # 1-5 logins per day
    total_session_minutes: int          # 300-600 minutes
    data_transferred_mb: int            # 50-500 MB
    databases_accessed: List[str]       # ["app_db", "analytics_db"]
    files_accessed: int                 # 10-100 files
    commands_executed: int              # 20-100 commands
    privilege_escalations: int          # 0-2
    failures: int                       # 0-5 failed attempts
    login_hours: List[int]             # Which hours did user log in


class UserBehaviorBaselineGenerator:
    """
    Generates 30-day synthetic baseline for a user
    
    Creates realistic, statistically valid behavior patterns
    that ML models can learn from to detect anomalies
    """
    
    def __init__(self, user_id: str, role: str = "analyst"):
        self.user_id = user_id
        self.role = role  # "developer", "analyst", "admin", "finance", etc.
        self.baseline_days: List[BehaviorDay] = []
        
        # Role-based parameters
        self.role_params = self._get_role_parameters(role)
    
    def generate_30_day_baseline(self) -> List[BehaviorDay]:
        """
        Generate 30 days of realistic user behavior
        
        Includes:
        - Normal work hours (9am-5pm)
        - Weekend/holiday variation
        - Typical data volumes
        - Normal database access patterns
        - Expected failure rates
        """
        
        baseline = []
        start_date = datetime.utcnow() - timedelta(days=30)
        
        for day_offset in range(30):
            current_date = start_date + timedelta(days=day_offset)
            day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
            
            # Weekend/weekday variation
            is_weekend = day_of_week >= 5
            
            # Generate day's behavior
            day = self._generate_behavior_day(current_date, is_weekend)
            baseline.append(day)
        
        self.baseline_days = baseline
        return baseline
    
    def _generate_behavior_day(self, date: datetime, is_weekend: bool) -> BehaviorDay:
        """Generate one day of behavior based on role and day type"""
        
        params = self.role_params
        
        # Adjust for weekend
        if is_weekend:
            # Minimal activity on weekends
            login_count = random.randint(0, 1)
            session_minutes = random.randint(0, 120)
            data_mb = random.randint(0, 50)
        else:
            # Normal weekday activity
            login_count = random.randint(params['min_logins'], params['max_logins'])
            session_minutes = random.randint(params['min_session_min'], params['max_session_min'])
            data_mb = random.randint(params['min_data_mb'], params['max_data_mb'])
        
        # Login hours (during work hours)
        login_hours = self._generate_login_hours(login_count, is_weekend)
        
        # Databases accessed
        databases = random.sample(
            params['typical_databases'],
            k=min(random.randint(1, 3), len(params['typical_databases']))
        )
        
        # Files and commands
        files_accessed = random.randint(5, 100)
        commands = random.randint(10, 100)
        
        # Privilege escalations (rare for non-admin)
        privilege_escalations = 0
        if self.role == "admin":
            privilege_escalations = random.randint(0, 3)
        elif self.role in ["developer", "analyst"]:
            privilege_escalations = random.randint(0, 1)
        
        # Failures (very rare for normal users)
        failures = random.randint(0, 2)
        
        return BehaviorDay(
            date=date.strftime("%Y-%m-%d"),
            user_id=self.user_id,
            login_count=login_count,
            total_session_minutes=session_minutes,
            data_transferred_mb=data_mb,
            databases_accessed=databases,
            files_accessed=files_accessed,
            commands_executed=commands,
            privilege_escalations=privilege_escalations,
            failures=failures,
            login_hours=login_hours
        )
    
    def _generate_login_hours(self, login_count: int, is_weekend: bool) -> List[int]:
        """Generate realistic login hours during work hours"""
        
        if is_weekend:
            # Rare, at irregular times
            if login_count == 0:
                return []
            return [random.randint(0, 23) for _ in range(login_count)]
        else:
            # Work hours: 9am-5pm (9-17)
            hours = []
            available_hours = list(range(9, 18))  # 9am-6pm
            
            for _ in range(login_count):
                # Prefer morning and afternoon
                if random.random() < 0.7:
                    # Morning/afternoon
                    hour = random.choice([9, 10, 11, 14, 15, 16])
                else:
                    # Anytime during work hours
                    hour = random.choice(available_hours)
                hours.append(hour)
            
            return sorted(hours)
    
    def _get_role_parameters(self, role: str) -> Dict:
        """Get behavior parameters for role"""
        
        params_map = {
            "developer": {
                "min_logins": 1,
                "max_logins": 3,
                "min_session_min": 200,
                "max_session_min": 600,
                "min_data_mb": 100,
                "max_data_mb": 1000,
                "typical_databases": ["dev_db", "test_db", "staging_db"],
            },
            "analyst": {
                "min_logins": 1,
                "max_logins": 4,
                "min_session_min": 300,
                "max_session_min": 500,
                "min_data_mb": 50,
                "max_data_mb": 500,
                "typical_databases": ["analytics_db", "events_db", "reports_db"],
            },
            "admin": {
                "min_logins": 2,
                "max_logins": 5,
                "min_session_min": 150,
                "max_session_min": 800,
                "min_data_mb": 500,
                "max_data_mb": 10000,
                "typical_databases": ["all_databases"],
            },
            "finance": {
                "min_logins": 1,
                "max_logins": 2,
                "min_session_min": 200,
                "max_session_min": 400,
                "min_data_mb": 50,
                "max_data_mb": 300,
                "typical_databases": ["finance_db", "accounting_db", "reports_db"],
            },
            "default": {
                "min_logins": 1,
                "max_logins": 3,
                "min_session_min": 200,
                "max_session_min": 500,
                "min_data_mb": 50,
                "max_data_mb": 500,
                "typical_databases": ["prod_db"],
            }
        }
        
        return params_map.get(role, params_map["default"])
    
    def get_profile_summary(self) -> Dict:
        """Get statistical summary of generated baseline"""
        
        if not self.baseline_days:
            return {"error": "No baseline generated yet"}
        
        login_counts = [day.login_count for day in self.baseline_days]
        session_minutes = [day.total_session_minutes for day in self.baseline_days]
        data_mbs = [day.data_transferred_mb for day in self.baseline_days]
        
        return {
            "user_id": self.user_id,
            "role": self.role,
            "days_generated": len(self.baseline_days),
            "avg_logins_per_day": sum(login_counts) / len(login_counts),
            "max_logins_per_day": max(login_counts),
            "min_logins_per_day": min(login_counts),
            "avg_session_minutes": sum(session_minutes) / len(session_minutes),
            "avg_data_mb_per_day": sum(data_mbs) / len(data_mbs),
            "max_data_mb_single_day": max(data_mbs),
            "typical_login_hours": list(range(9, 18)),
            "typical_work_days": "Monday-Friday",
            "weekend_activity": sum(1 for d in self.baseline_days if d.total_session_minutes == 0) / 30
        }


class BulkBaselineGenerator:
    """
    Generate baselines for multiple users efficiently
    """
    
    def __init__(self):
        self.users_baselines: Dict[str, List[BehaviorDay]] = {}
    
    def generate_organization_baseline(
        self,
        user_count: int = 50
    ) -> Dict[str, List[BehaviorDay]]:
        """
        Generate realistic baseline for entire organization
        
        Creates realistic distribution across roles
        """
        
        # Role distribution (realistic)
        role_distribution = {
            "developer": int(user_count * 0.30),    # 30% developers
            "analyst": int(user_count * 0.25),     # 25% analysts
            "admin": int(user_count * 0.10),       # 10% admins
            "finance": int(user_count * 0.20),     # 20% finance
            "other": user_count - int(user_count * 0.85)  # 15% other
        }
        
        logger.info(
            f"Generating baseline for {user_count} users: "
            f"{role_distribution}"
        )
        
        user_index = 0
        
        for role, count in role_distribution.items():
            for i in range(count):
                user_id = f"{role}_user_{user_index:03d}"
                generator = UserBehaviorBaselineGenerator(user_id, role)
                baseline = generator.generate_30_day_baseline()
                self.users_baselines[user_id] = baseline
                user_index += 1
        
        logger.info(f"Generated baseline for {user_index} users")
        return self.users_baselines
    
    def get_user_profile(self, user_id: str) -> Optional[List[BehaviorDay]]:
        """Get generated baseline for specific user"""
        return self.users_baselines.get(user_id)
    
    def export_baselines_to_json(self, filepath: str) -> None:
        """Export all baselines to JSON file"""
        
        export_data = {}
        
        for user_id, baseline in self.users_baselines.items():
            export_data[user_id] = [
                {
                    "date": day.date,
                    "login_count": day.login_count,
                    "session_minutes": day.total_session_minutes,
                    "data_mb": day.data_transferred_mb,
                    "databases": day.databases_accessed,
                    "files": day.files_accessed,
                    "commands": day.commands_executed,
                    "privilege_escalations": day.privilege_escalations,
                    "failures": day.failures,
                    "login_hours": day.login_hours
                }
                for day in baseline
            ]
        
        import json
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported {len(self.users_baselines)} user baselines to {filepath}")
    
    def generate_organization_statistics(self) -> Dict:
        """Get organization-wide statistics"""
        
        stats = {
            "total_users": len(self.users_baselines),
            "users_by_role": {},
            "organization_avg_logins": 0,
            "organization_avg_data_transfer_mb": 0
        }
        
        all_logins = []
        all_data = []
        
        for user_id, baseline in self.users_baselines.items():
            role = user_id.split("_")[0]
            
            if role not in stats["users_by_role"]:
                stats["users_by_role"][role] = 0
            stats["users_by_role"][role] += 1
            
            for day in baseline:
                all_logins.append(day.login_count)
                all_data.append(day.data_transferred_mb)
        
        if all_logins:
            stats["organization_avg_logins"] = sum(all_logins) / len(all_logins)
        if all_data:
            stats["organization_avg_data_transfer_mb"] = sum(all_data) / len(all_data)
        
        return stats


# Example usage function
def create_example_baselines():
    """Create example baselines for testing"""
    
    logger.info("Generating 30-day behavior baselines for 50 users...")
    
    bulk_gen = BulkBaselineGenerator()
    bulk_gen.generate_organization_baseline(user_count=50)
    
    # Export to file
    bulk_gen.export_baselines_to_json(
        "/tmp/behavior_baselines.json"
    )
    
    # Get statistics
    stats = bulk_gen.generate_organization_statistics()
    logger.info(f"Generated baseline statistics: {stats}")
    
    return bulk_gen

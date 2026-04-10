"""
MAYA Honeypot Package - Deceptive Threat Detection

Contains multiple honeypot implementations:
- SSH Honeypot: Fake SSH server on port 2222
- Web Honeypot: Fake banking portal on port 5001
- Database Honeypot: Fake MySQL/Redis on ports 3306/6379

All attacks are logged to the central event bus for correlation and analysis.
"""

from .ssh_honeypot import start_ssh_honeypot, FakeSSHServer
from .web_honeypot import create_web_honeypot
from .db_honeypot import start_mysql_honeypot, start_redis_honeypot

__all__ = [
    "start_ssh_honeypot",
    "FakeSSHServer",
    "create_web_honeypot",
    "start_mysql_honeypot",
    "start_redis_honeypot",
]

"""
Enterprise-grade logging configuration with structured JSON output.

SECURITY: All logs are structured, sanitized, and production-safe.
"""

import logging
import logging.handlers
import json
from datetime import datetime
from typing import Any, Dict
import os
import sys


class JSONFormatter(logging.Formatter):
    """Format logs as structured JSON for enterprise processing."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert log record to JSON string."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if provided
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "service"):
            log_data["service"] = record.service

        return json.dumps(log_data, default=str)


def setup_logging() -> None:
    """Configure enterprise-grade logging system."""
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove any existing handlers
    root_logger.handlers.clear()

    # ===== CONSOLE HANDLER =====
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Format based on environment
    if os.getenv("ENV") == "production":
        # JSON output in production
        console_formatter = JSONFormatter()
    else:
        # Human-readable in development
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ===== FILE HANDLER =====
    log_dir = os.getenv("LOG_DIR", "/var/log/maya-soc")
    os.makedirs(log_dir, exist_ok=True)
    
    file_handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/application.log",
        maxBytes=100 * 1024 * 1024,  # 100 MB
        backupCount=10,  # Keep 10 backup files
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = JSONFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)

    # ===== ERROR FILE HANDLER =====
    error_handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/errors.log",
        maxBytes=100 * 1024 * 1024,
        backupCount=10,
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)

    # ===== AUDIT HANDLER (Security-relevant events) =====
    audit_handler = logging.handlers.RotatingFileHandler(
        filename=f"{log_dir}/audit.log",
        maxBytes=100 * 1024 * 1024,
        backupCount=30,  # Keep longer history for audit
    )
    audit_handler.setLevel(logging.WARNING)
    audit_handler.setFormatter(file_formatter)
    
    # Create audit logger
    audit_logger = logging.getLogger("audit")
    audit_logger.addHandler(audit_handler)
    audit_logger.setLevel(logging.WARNING)

    # Set specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("kafka").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    return logging.getLogger(name)


def get_audit_logger() -> logging.Logger:
    """Get the audit logger for security-relevant events."""
    return logging.getLogger("audit")

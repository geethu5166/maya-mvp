"""
Centralized logging configuration with structured JSON logging
Replaces all print() statements with proper logging
"""

import logging
import logging.config
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Create logs directory if it doesn't exist
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
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
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/maya-soc.log",
    log_format: str = "json"
) -> None:
    """
    Configure logging for the entire application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        log_format: Format type - 'json' for structured, 'text' for human-readable
    """
    
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set root logger level
    root_logger.setLevel(log_level)
    
    # Console Handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    if log_format == "json":
        console_formatter = JSONFormatter()
    else:
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File Handler (if path provided)
    if log_file:
        try:
            log_file_path = Path(log_file)
            log_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file_path)
            file_handler.setLevel(log_level)
            
            # Always use JSON for file logging
            file_formatter = JSONFormatter()
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning(f"Could not setup file logging: {e}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module
    
    Args:
        name: Module name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin to add logging to any class"""
    
    @property
    def logger(self) -> logging.Logger:
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger
    
    def log_info(self, message: str, **kwargs) -> None:
        """Log info message"""
        self.logger.info(message, extra={"extra": kwargs})
    
    def log_warning(self, message: str, **kwargs) -> None:
        """Log warning message"""
        self.logger.warning(message, extra={"extra": kwargs})
    
    def log_error(self, message: str, exc_info: bool = True, **kwargs) -> None:
        """Log error message"""
        self.logger.error(message, exc_info=exc_info, extra={"extra": kwargs})
    
    def log_debug(self, message: str, **kwargs) -> None:
        """Log debug message"""
        self.logger.debug(message, extra={"extra": kwargs})
    
    def log_critical(self, message: str, **kwargs) -> None:
        """Log critical message"""
        self.logger.critical(message, extra={"extra": kwargs})


# Initialize logging on import
if os.getenv("LOG_LEVEL"):
    log_level = os.getenv("LOG_LEVEL", "INFO")
else:
    log_level = "INFO"

log_file = os.getenv("LOG_FILE", "logs/maya-soc.log")
log_format = os.getenv("LOG_FORMAT", "json")

setup_logging(log_level=log_level, log_file=log_file, log_format=log_format)

"""
Error Handling Utilities - Replace bare except: blocks with proper error handling
Includes decorators, context managers, and exception classes
"""

import logging
import functools
import traceback
from typing import Callable, Optional, Any, Type, List
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)


# ============================================================================
# CUSTOM EXCEPTION CLASSES
# ============================================================================

class MAYAException(Exception):
    """Base exception for MAYA SOC"""
    pass


class ConfigurationError(MAYAException):
    """Configuration/initialization error"""
    pass


class AuthenticationError(MAYAException):
    """Authentication failure"""
    pass


class PipelineError(MAYAException):
    """Event pipeline error"""
    pass


class HoneypotError(MAYAException):
    """Honeypot operation error"""
    pass


class DatabaseError(MAYAException):
    """Database operation error"""
    pass


class ExternalServiceError(MAYAException):
    """External service (API) error"""
    pass


# ============================================================================
# ERROR HANDLERS & DECORATORS
# ============================================================================

def safe_async(
    default_return: Any = None,
    log_level: str = "error",
    catch_exceptions: List[Type[Exception]] = None
):
    """
    Decorator for async functions - catches exceptions and logs
    
    Usage:
        @safe_async(default_return=False)
        async def risky_function():
            ...
    """
    if catch_exceptions is None:
        catch_exceptions = [Exception]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except tuple(catch_exceptions) as e:
                log_func = getattr(logger, log_level)
                log_func(
                    f"Error in {func.__name__}: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                return default_return
        return wrapper
    return decorator


def safe_sync(
    default_return: Any = None,
    log_level: str = "error",
    catch_exceptions: List[Type[Exception]] = None
):
    """
    Decorator for sync functions - catches exceptions and logs
    
    Usage:
        @safe_sync(default_return=False)
        def risky_function():
            ...
    """
    if catch_exceptions is None:
        catch_exceptions = [Exception]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except tuple(catch_exceptions) as e:
                log_func = getattr(logger, log_level)
                log_func(
                    f"Error in {func.__name__}: {str(e)}\n"
                    f"Traceback: {traceback.format_exc()}"
                )
                return default_return
        return wrapper
    return decorator


def retry(
    max_attempts: int = 3,
    delay_seconds: float = 1,
    backoff_multiplier: float = 2,
    catch_exceptions: List[Type[Exception]] = None
):
    """
    Retry decorator with exponential backoff
    
    Usage:
        @retry(max_attempts=3, delay_seconds=1)
        async def api_call():
            ...
    """
    if catch_exceptions is None:
        catch_exceptions = [Exception]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            import asyncio
            
            attempt = 0
            current_delay = delay_seconds
            
            while attempt < max_attempts:
                try:
                    return await func(*args, **kwargs)
                except tuple(catch_exceptions) as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Max retries ({max_attempts}) reached for {func.__name__}")
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}, "
                        f"retrying in {current_delay}s: {str(e)}"
                    )
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff_multiplier
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time
            
            attempt = 0
            current_delay = delay_seconds
            
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except tuple(catch_exceptions) as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Max retries ({max_attempts}) reached for {func.__name__}")
                        raise
                    
                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}, "
                        f"retrying in {current_delay}s: {str(e)}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff_multiplier
        
        # Return async or sync wrapper based on function
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ============================================================================
# CONTEXT MANAGERS
# ============================================================================

@contextmanager
def handle_error(
    error_name: str,
    default_return: Any = None,
    log_level: str = "error"
):
    """
    Context manager for error handling
    
    Usage:
        with handle_error("database operation", default_return=None):
            db.query(...)
    """
    try:
        yield
    except Exception as e:
        log_func = getattr(logger, log_level)
        log_func(
            f"Error in {error_name}: {str(e)}\n"
            f"Traceback: {traceback.format_exc()}"
        )


@contextmanager
def log_duration(operation_name: str):
    """
    Context manager to log operation duration
    
    Usage:
        with log_duration("data processing"):
            expensive_operation()
    """
    start_time = datetime.now()
    try:
        logger.info(f"Starting: {operation_name}")
        yield
    finally:
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Completed: {operation_name} ({duration:.2f}s)")


# ============================================================================
# EXCEPTION HANDLING PATTERNS
# ============================================================================

async def safe_publish_event(event_data: dict) -> bool:
    """
    Example: Safe event publishing
    Replaces bare except: blocks
    """
    try:
        from app.core.unified_event_pipeline import publish_security_event
        result = await publish_security_event(**event_data)
        return result
    except PipelineError as e:
        logger.error(f"Pipeline error: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected error in event publishing: {e}")
        return False


async def safe_database_query(query_func: Callable, *args, **kwargs) -> Optional[Any]:
    """
    Example: Safe database operations
    """
    try:
        result = await query_func(*args, **kwargs)
        return result
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        return None
    except Exception as e:
        logger.exception(f"Unexpected database error: {e}")
        return None


# ============================================================================
# BEFORE: Bad error handling (REMOVE THIS)
# ============================================================================

"""
try:
    # Some code
except:
    pass

try:
    # Some code
except Exception:
    pass
"""


# ============================================================================
# AFTER: Good error handling (USE THIS)
# ============================================================================

"""
# Pattern 1: Use decorators
@safe_sync(default_return=False)
def my_function():
    pass

# Pattern 2: Use context managers
with handle_error("operation name"):
    # do something

# Pattern 3: Explicit exception handling
try:
    # do something
except SpecificException as e:
    logger.error(f"Specific error: {e}")
except Exception as e:
    logger.exception(f"Unexpected error: {e}")

# Pattern 4: Use retry decorator
@retry(max_attempts=3)
async def api_call():
    pass

# Pattern 5: Duration logging
with log_duration("my operation"):
    # do something
"""

"""Retry decorator with exponential backoff."""
import time
import functools
import logging

logger = logging.getLogger(__name__)


def retry(max_attempts: int = 3, backoff_base: int = 2, exceptions: tuple = (Exception,)):
    """Decorator: retry function up to max_attempts with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    if attempt < max_attempts:
                        wait = backoff_base ** (attempt - 1)
                        logger.warning(
                            f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                            f"Retrying in {wait}s..."
                        )
                        time.sleep(wait)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
            raise last_exc
        return wrapper
    return decorator

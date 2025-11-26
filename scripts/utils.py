"""Shared utility functions for Copilot triage and grooming scripts."""

from __future__ import annotations

import random
import time
from functools import wraps
from typing import Callable, TypeVar

import requests

F = TypeVar("F", bound=Callable)


def retry_on_failure(
    max_retries: int = 5,
    backoff_factor: float = 2.0,
    base_delay: float = 1.0,
    logger=None,
):
    """Decorator to retry a function on failure with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 5)
        backoff_factor: Multiplier for exponential backoff (default: 2.0)
        base_delay: Initial delay in seconds (default: 1.0)
        logger: Optional logger instance for warnings/errors

    Catches requests.ConnectionError, requests.Timeout, and
    requests.HTTPError and retries with exponential backoff plus jitter.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import sys

            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (
                    requests.ConnectionError,
                    requests.Timeout,
                    requests.HTTPError,
                ) as e:
                    last_exception = e
                    if attempt < max_retries:
                        backoff = backoff_factor ** (attempt - 1)
                        sleep_time = base_delay * backoff
                        sleep_time += random.uniform(0, 2)
                        msg = (
                            f"Attempt {attempt} failed: {e}. "
                            f"Retrying in {sleep_time:.1f}s..."
                        )
                        if logger:
                            logger.warning(msg)
                        else:
                            print(msg, file=sys.stderr)
                        time.sleep(sleep_time)
                    else:
                        msg = (
                            f"Max retries ({max_retries}) exceeded "
                            f"for {func.__name__}"
                        )
                        if logger:
                            logger.error(msg)
                        else:
                            print(msg, file=sys.stderr)
                        raise last_exception

        return wrapper

    return decorator

"""Shell utility functions for executing commands and managing processes."""

from __future__ import annotations

import asyncio
import functools
from collections.abc import Callable
from typing import Any, TypeVar

import structlog

logger = structlog.get_logger(__name__)


T = TypeVar("T")


def to_async(func: Callable[..., T]) -> Callable[..., asyncio.Future[T]]:
    """Convert a synchronous function to an asynchronous one.

    Args:
        func: The synchronous function to convert

    Returns:
        An asynchronous version of the function
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> asyncio.Future[T]:
        return asyncio.get_event_loop().run_in_executor(
            None, lambda: func(*args, **kwargs)
        )

    return wrapper


async_ = to_async  # Alias for backward compatibility

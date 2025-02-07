"""UUID utility functions."""

from __future__ import annotations

import uuid
from typing import Any


def is_valid_uuid(val: Any) -> bool:
    """Check if a value is a valid UUID.

    Args:
        val: Value to check for UUID validity

    Returns:
        bool: True if value is a valid UUID, False otherwise
    """
    try:
        uuid.UUID(str(val))
        return True
    except (ValueError, TypeError):
        return False

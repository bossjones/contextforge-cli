from __future__ import annotations

import os
from typing import Any, Optional


def environ_get(key: str, default: Any = None) -> Any:
    """Get environment variable value with default fallback.

    Args:
        key: Environment variable name
        default: Default value if environment variable is not set

    Returns:
        Any: Environment variable value or default
    """
    retval = os.environ.get(key, default=default)

    if key not in os.environ:
        print(
            f"environ_get: Env Var not defined! Using default! Attempted={key}, default={default}"
        )

    return retval


def environ_append(
    key: str, value: str, separator: str = " ", force: bool = False
) -> None:
    """Append value to environment variable with separator.

    Args:
        key: Environment variable name
        value: Value to append
        separator: Separator between values
        force: Whether to force the operation (unused)
    """
    old_value = os.environ.get(key)
    if old_value is not None:
        value = old_value + separator + value
    os.environ[key] = value


def environ_prepend(
    key: str, value: str, separator: str = " ", force: bool = False
) -> None:
    """Prepend value to environment variable with separator.

    Args:
        key: Environment variable name
        value: Value to prepend
        separator: Separator between values
        force: Whether to force the operation (unused)
    """
    old_value = os.environ.get(key)
    if old_value is not None:
        value = value + separator + old_value
    os.environ[key] = value


def environ_remove(
    key: str, value: str, separator: str = ":", force: bool = False
) -> None:
    """Remove value from environment variable.

    Args:
        key: Environment variable name
        value: Value to remove
        separator: Separator between values
        force: Whether to force the operation (unused)
    """
    old_value = os.environ.get(key)
    if old_value is not None:
        old_value_split = old_value.split(separator)
        value_split = [x for x in old_value_split if x != value]
        value = separator.join(value_split)
    os.environ[key] = value


def environ_set(key: str, value: str) -> None:
    """Set environment variable value.

    Args:
        key: Environment variable name
        value: Value to set
    """
    os.environ[key] = value


def path_append(value: str) -> None:
    """Append directory to PATH if it exists.

    Args:
        value: Directory path to append
    """
    if os.path.exists(value):
        environ_append("PATH", value, ":")


def path_prepend(value: str, force: bool = False) -> None:
    """Prepend directory to PATH if it exists.

    Args:
        value: Directory path to prepend
        force: Whether to force the operation (unused)
    """
    if os.path.exists(value):
        environ_prepend("PATH", value, ":", force)

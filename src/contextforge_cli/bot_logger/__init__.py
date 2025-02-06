# #!/usr/bin/env python3

# """
# Logging utilities for the SandboxAgent project.

# This module provides functions and utilities for configuring and managing logging in the SandboxAgent project.
# It includes functions for setting up the global logger, handling exceptions, and filtering log messages.

# Functions:
#     global_log_config(log_level: LOG_LEVEL, json: bool = False) -> None:
#         Configure the global logger with the specified log level and format.

#     get_logger(name: str = "contextforge_cli") -> Logger:
#         Get a logger instance with the specified name.

#     _log_exception(exc: BaseException, dev_mode: bool = False) -> None:
#         Log an exception with the appropriate level based on the dev_mode setting.

#     _log_warning(exc: BaseException, dev_mode: bool = False) -> None:
#         Log a warning with the appropriate level based on the dev_mode setting.

#     filter_out_serialization_errors(record: dict[str, Any]) -> bool:
#         Filter out log messages related to serialization errors.

#     filter_out_modules(record: dict[str, Any]) -> bool:
#         Filter out log messages from the standard logging module.

# Constants:
#     LOGURU_FILE_FORMAT: str
#         The log format string for file logging.

#     NEW_logger_FORMAT: str
#         The new log format string for console logging.

#     LOG_LEVEL: Literal
#         The available log levels.

#     MASKED: str
#         A constant string used to mask sensitive data in logs.

# Classes:
#     Pii(str):
#         A custom string class that masks sensitive data in logs based on the log_pii setting.
# """
# # pylint: disable=no-member
# # pylint: disable=consider-using-tuple
# # pylint: disable=eval-used,no-member
# # pyright: ignore[reportOperatorIssue]
# # pyright: ignore[reportOptionalIterable]
# # SOURCE: https://betterstack.com/community/guides/logging/loguru/

# # FIXME: https://github.com/sweepai/sweep/blob/7d93c612568b8febd4aaf3c75810794bc10c09ae/sweepai/utils/event_logger.py#L7
# # FIXME: https://github.com/sweepai/sweep/blob/7d93c612568b8febd4aaf3c75810794bc10c09ae/sweepai/utils/event_logger.py#L7
# # FIXME: https://github.com/sweepai/sweep/blob/7d93c612568b8febd4aaf3c75810794bc10c09ae/sweepai/utils/event_logger.py#L7
# # FIXME: https://github.com/sweepai/sweep/blob/7d93c612568b8febd4aaf3c75810794bc10c09ae/sweepai/utils/event_logger.py#L7
# # FIXME: https://github.com/sweepai/sweep/blob/7d93c612568b8febd4aaf3c75810794bc10c09ae/sweepai/utils/event_logger.py#L7
# # FIXME: https://github.com/sweepai/sweep/blob/7d93c612568b8febd4aaf3c75810794bc10c09ae/sweepai/utils/event_logger.py#L7
# # FIXME: https://github.com/sweepai/sweep/blob/7d93c612568b8febd4aaf3c75810794bc10c09ae/sweepai/utils/event_logger.py#L7
# # FIXME: https://github.com/sweepai/sweep/blob/7d93c612568b8febd4aaf3c75810794bc10c09ae/sweepai/utils/event_logger.py#L7
# # FIXME: https://github.com/sweepai/sweep/blob/7d93c612568b8febd4aaf3c75810794bc10c09ae/sweepai/utils/event_logger.py#L7

# from __future__ import annotations

# import contextvars
# import functools
# import gc
# import inspect
# import logging
# import multiprocessing
# import os
# import re
# import sys
# import time

# from datetime import UTC, datetime, timezone
# from logging import Logger, LogRecord
# from pathlib import Path
# from pprint import pformat
# from sys import stdout
# from time import process_time
# from types import FrameType
# from typing import TYPE_CHECKING, Any, Deque, Dict, Literal, Optional, Union, cast

# import loguru


from __future__ import annotations

import logging

import structlog

from contextforge_cli.models.loggers import LoggerModel, LoggerPatch

logger = structlog.get_logger(__name__)


def get_lm_from_tree(loggertree: LoggerModel, find_me: str) -> LoggerModel | None:
    """Recursively search for a logger model in the logger tree.

    Args:
        loggertree: The root logger model to search from.
        find_me: The name of the logger model to find.

    Returns:
        The found logger model, or None if not found.
    """
    if find_me == loggertree.name:
        print("Found")
        return loggertree
    else:
        for ch in loggertree.children:
            print(f"Looking in: {ch.name}")
            if i := get_lm_from_tree(ch, find_me):
                return i
    return None


def generate_tree() -> LoggerModel:
    """Generate a tree of logger models.

    Returns:
        The root logger model of the generated tree.
    """
    rootm = LoggerModel(
        name="root", level=logging.getLogger().getEffectiveLevel(), children=[]
    )
    nodesm: dict[str, LoggerModel] = {}
    items = sorted(logging.root.manager.loggerDict.items())  # type: ignore
    for name, loggeritem in items:
        if isinstance(loggeritem, logging.PlaceHolder):
            nodesm[name] = nodem = LoggerModel(name=name, children=[])
        else:
            nodesm[name] = nodem = LoggerModel(
                name=name, level=loggeritem.getEffectiveLevel(), children=[]
            )
        i = name.rfind(".", 0, len(name) - 1)
        parentm = rootm if i == -1 else nodesm[name[:i]]
        parentm.children.append(nodem)
    return rootm

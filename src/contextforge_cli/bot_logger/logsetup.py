# pyright: reportAttributeAccessIssue=false
# pyright: reportInvalidTypeForm=false
# pyright: reportUndefinedVariable=false
# pyright: reportUnusedFunction=false

from __future__ import annotations

import logging
import logging.config
import multiprocessing
import sys
from typing import Any

import structlog
from structlog.contextvars import (
    bind_contextvars,
    clear_contextvars,
)
from structlog.stdlib import BoundLogger
from structlog.typing import Processor

# so we have logger names
structlog.stdlib.recreate_defaults()

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


def get_log_level(level: str | int) -> int:
    """Convert a log level string to its corresponding logging level value.

    This function takes a string or integer log level and returns the corresponding
    logging level value. It supports both string names (e.g., 'INFO', 'DEBUG') and
    integer values.

    Args:
        level: The log level as a string (e.g., 'INFO', 'DEBUG') or integer

    Returns:
        int: The corresponding logging level value

    Raises:
        ValueError: If the log level string is not valid
        TypeError: If the level is not a string or integer
    """
    if isinstance(level, int):
        if level < 0:
            raise ValueError(
                f"Invalid level value, it should be a positive integer, not: {level}"
            )
        return level

    if not isinstance(level, str):
        raise TypeError(
            f"Invalid level, it should be an integer or a string, not: '{type(level).__name__}'"
        )

    # Convert to upper case for case-insensitive comparison
    level_upper = level.upper()

    # Map of level names to level numbers
    level_map = {
        "CRITICAL": logging.CRITICAL,  # 50
        "FATAL": logging.FATAL,  # 50
        "ERROR": logging.ERROR,  # 40
        "WARNING": logging.WARNING,  # 30
        "WARN": logging.WARN,  # 30
        "INFO": logging.INFO,  # 20
        "DEBUG": logging.DEBUG,  # 10
        "NOTSET": logging.NOTSET,  # 0
    }

    try:
        return level_map[level_upper]
    except KeyError:
        raise ValueError(f"Invalid log level: '{level}'") from None


def configure_logging(
    enable_json_logs: bool = False,
    log_level: str = "INFO",
    third_party_loggers: dict[str, str] | None = None,
    environment: str = "development",
) -> dict[str, Any]:
    """Configure structured logging with comprehensive async support and third-party integration.

    This function sets up a unified logging system following structlog best practices:
    1. Environment-aware configuration (development vs production)
    2. Proper async context handling with contextvars
    3. Performance-optimized processor chains
    4. Comprehensive error and exception handling
    5. Integration with standard library logging
    6. Support for both development (pretty) and production (JSON) output
    7. Proper timestamp handling in UTC
    8. Canonical log lines support through bound loggers

    Args:
        enable_json_logs: If True, outputs logs in JSON format. Otherwise, uses colored console output.
        log_level: The minimum log level to capture.
        third_party_loggers: Dict of logger names and their minimum levels to configure.
        environment: The runtime environment ("development", "production", "testing")

    Returns:
        dict[str, Any]: The current structlog configuration
    """
    # Default third-party logger configuration
    default_third_party = {
        "discord": "WARNING",
        "discord.client": "WARNING",
        "discord.gateway": "WARNING",
        "aiohttp": "WARNING",
        "asyncio": "WARNING",
        "urllib3": "WARNING",
        "requests": "WARNING",
        "PIL": "WARNING",
    }

    if third_party_loggers:
        default_third_party.update(third_party_loggers)

    # Configure third-party loggers
    for logger_name, level in default_third_party.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(get_log_level(level))

    # Clear any existing context for clean configuration
    clear_contextvars()

    def get_processor_chain(enable_dev_processors: bool = False) -> list[Processor]:
        """Build the processor chain based on environment needs.

        Follows structlog's best practices for processor ordering and optimization.
        See: https://www.structlog.org/en/stable/logging-best-practices.html

        Args:
            enable_dev_processors: Whether to include development-specific processors

        Returns:
            List of configured processors
        """
        # Core processors that are always needed
        processors: list[Processor] = [
            # Filter by level first for performance
            structlog.stdlib.filter_by_level,
            # Context management
            structlog.contextvars.merge_contextvars,
            # Add basic event metadata
            structlog.processors.add_log_level,
            structlog.stdlib.add_logger_name,
            # Format any positional arguments
            structlog.stdlib.PositionalArgumentsFormatter(),
            # Add timestamps in UTC
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            # Add stack information for errors
            structlog.processors.StackInfoRenderer(),
            # Handle exceptions
            structlog.processors.format_exc_info,
            # Decode any bytes to strings
            structlog.processors.UnicodeDecoder(),
        ]

        # Development-specific processors
        if enable_dev_processors and environment == "development":
            processors.append(
                structlog.processors.CallsiteParameterAdder(
                    {
                        structlog.processors.CallsiteParameter.PATHNAME,
                        structlog.processors.CallsiteParameter.FILENAME,
                        structlog.processors.CallsiteParameter.MODULE,
                        structlog.processors.CallsiteParameter.FUNC_NAME,
                        structlog.processors.CallsiteParameter.LINENO,
                        structlog.processors.CallsiteParameter.THREAD,
                        structlog.processors.CallsiteParameter.THREAD_NAME,
                        structlog.processors.CallsiteParameter.PROCESS,
                        structlog.processors.CallsiteParameter.PROCESS_NAME,
                    }
                )
            )

        return processors

    # Get shared processors
    shared_processors = get_processor_chain(not enable_json_logs)

    def get_renderer(enable_json_logs: bool) -> Processor:
        """Get the appropriate renderer based on environment.

        Args:
            enable_json_logs: Whether to use JSON logging

        Returns:
            Configured renderer processor
        """
        if environment == "testing":
            # Return a renderer that accepts sort_keys but just passes through the event dict
            return lambda _, __, event_dict, **_kw: event_dict

        if enable_json_logs or environment == "production":
            return structlog.processors.JSONRenderer(
                sort_keys=False,
                serializer=lambda obj: str(
                    obj
                ),  # Simple serializer that handles non-JSON types
            )

        return structlog.dev.ConsoleRenderer(
            colors=True,
            sort_keys=True,
        )

    # Get the appropriate renderer
    renderer = get_renderer(enable_json_logs)
    if enable_json_logs and environment != "testing":
        shared_processors.append(structlog.processors.format_exc_info)

    # Configure root logger with handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(get_log_level(log_level))

    # Remove any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create stdout handler for INFO and below
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO)
    root_logger.addHandler(stdout_handler)

    # Create stderr handler for WARNING and above
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    root_logger.addHandler(stderr_handler)

    # Configure structlog with performance optimizations
    structlog.configure(
        processors=shared_processors
        + [
            renderer,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(get_log_level(log_level)),
        cache_logger_on_first_use=environment != "testing",  # Disable caching for tests
    )

    return structlog.get_config()


def get_logger(name: str) -> BoundLogger:
    """Get a configured logger instance.

    This function returns a properly configured structlog logger instance.
    It's safe to call this at module level since it returns a lazy proxy
    that gets properly configured on first use.

    Args:
        name: The name for the logger, typically __name__

    Returns:
        A configured structlog logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("message", key="value")
    """
    return structlog.get_logger(name)


def reset_logging() -> None:
    """Reset logging configuration to default state.

    This is particularly useful in tests to ensure a clean slate between test cases.
    It:
    1. Clears all context variables
    2. Resets structlog configuration
    3. Cleans up any bound loggers

    Example:
        >>> def test_logging():
        ...     reset_logging()
        ...     configure_logging(environment="testing")
        ...     # Run test...
    """
    clear_contextvars()
    structlog.reset_defaults()
    # Recreate stdlib defaults for logger names
    structlog.stdlib.recreate_defaults()


def configure_test_logging() -> dict[str, Any]:
    """Configure logging specifically for testing.

    Sets up a test-optimized logging configuration that:
    1. Uses a capturing logger for test verification
    2. Disables caching for test isolation
    3. Enables all processors for thorough testing
    4. Sets DEBUG level for maximum visibility

    Returns:
        dict[str, Any]: The test logging configuration

    Example:
        >>> def test_feature():
        ...     configure_test_logging()
        ...     logger = get_logger(__name__)
        ...     # Run test...
    """
    # Clear any existing context for clean configuration
    clear_contextvars()

    # Configure with test-specific processors
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # No renderer in test mode - just return the event dict
            lambda _, __, event_dict, **_kw: event_dict,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=False,  # Important for test isolation
    )

    return structlog.get_config()


if __name__ == "__main__":
    import rich

    # Example usage and testing
    logger = structlog.get_logger(__name__)
    configure_logging(enable_json_logs=False, log_level="DEBUG")
    logger = structlog.get_logger(__name__)
    rich.print(structlog.get_config())

    import bpdb

    bpdb.set_trace()

    def worker_process(name: str) -> None:
        """Example worker process function.

        Args:
            name: Name of the worker
        """
        proc_logger = get_logger(f"worker.{name}")

        # Clear context for this process
        clear_contextvars()

        # Bind process-specific context
        bind_contextvars(worker_name=name, worker_type="example")

        proc_logger.info(f"Worker {name} starting")

        try:
            # Simulate some work
            1 / 0
        except Exception as e:
            proc_logger.error("Worker error", exc_info=e)

        proc_logger.info(f"Worker {name} finished")

    # Test in main process
    logger = get_logger("test_logger")
    clear_contextvars()

    # Bind some context variables that will be included in all log entries
    bind_contextvars(app_version="1.0.0", environment="development")

    # Start some worker processes
    processes = []
    for i in range(3):
        p = multiprocessing.Process(target=worker_process, args=(f"worker_{i}",))
        processes.append(p)
        p.start()

    # Test structured logging while workers run
    logger.info("Main process running", num_workers=len(processes))

    # Wait for all processes
    for p in processes:
        p.join()

    logger.info("All workers finished")

    # Clear context at the end
    clear_contextvars()

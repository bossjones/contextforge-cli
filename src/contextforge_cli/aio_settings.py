# pylint: disable=no-member
# pylint: disable=no-name-in-module
# pylint: disable=no-value-for-parameter
# pylint: disable=possibly-used-before-assignment
# pyright: reportAttributeAccessIssue=false
# pyright: reportConstantRedefinition=true
# pyright: reportInvalidTypeForm=false
# pyright: reportMissingTypeStubs=false
# pyright: reportUndefinedVariable=false

from __future__ import annotations

import enum
import pathlib

from datetime import timedelta, timezone
from typing import Any


from pydantic_settings import BaseSettings, SettingsConfigDict
from rich.console import Console


def democracy_user_agent() -> str:
    """Get a common user agent"""
    return "contextforge-cli/0.0.1"


# Get rid of warning
# USER_AGENT environment variable not set, consider setting it to identify your requests.
# os.environ["USER_AGENT"] = democracy_user_agent()

TIMEZONE = timezone(timedelta(hours=-5), name="America/New_York")


class SettingsError(Exception):
    """Base exception for all settings-related errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize the settings error.

        Args:
            message: The error message
            context: Additional context about the error
        """
        self.context = context or {}
        super().__init__(message)


class ValidationError(SettingsError):
    """Raised when settings validation fails."""

    def __init__(
        self,
        message: str,
        field_name: str,
        invalid_value: Any,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the validation error.

        Args:
            message: The error message
            field_name: Name of the field that failed validation
            invalid_value: The value that failed validation
            context: Additional context about the error
        """
        self.field_name = field_name
        self.invalid_value = invalid_value
        super().__init__(
            f"{message} (field: {field_name}, value: {invalid_value})", context
        )


class ModelConfigError(SettingsError):
    """Raised when there are issues with model configuration."""

    def __init__(
        self, message: str, model_name: str, context: dict[str, Any] | None = None
    ) -> None:
        """Initialize the model configuration error.

        Args:
            message: The error message
            model_name: Name of the model with configuration issues
            context: Additional context about the error
        """
        self.model_name = model_name
        super().__init__(f"{message} (model: {model_name})", context)


class SecurityError(SettingsError):
    """Raised when there are security-related issues with settings."""

    def __init__(
        self, message: str, setting_name: str, context: dict[str, Any] | None = None
    ) -> None:
        """Initialize the security error.

        Args:
            message: The error message
            setting_name: Name of the setting with security issues
            context: Additional context about the error
        """
        self.setting_name = setting_name
        super().__init__(
            f"Security error with setting '{setting_name}': {message}", context
        )


class ConfigurationError(SettingsError):
    """Raised when there are issues with the overall configuration."""

    def __init__(
        self, message: str, config_section: str, context: dict[str, Any] | None = None
    ) -> None:
        """Initialize the configuration error.

        Args:
            message: The error message
            config_section: Section of configuration with issues
            context: Additional context about the error
        """
        self.config_section = config_section
        super().__init__(
            f"Configuration error in section '{config_section}': {message}", context
        )


def normalize_settings_path(file_path: str) -> str:
    """Normalize file paths with tilde expansion.

    Converts paths starting with ~ to absolute paths using the user's home directory.

    Args:
        file_path: Path to normalize, may start with ~

    Returns:
        str: Normalized absolute path
    """
    return (
        str(pathlib.Path(file_path).expanduser())
        if file_path.startswith("~")
        else file_path
    )


class LogLevel(str, enum.Enum):
    """Possible log levels for application logging.

    Standard Python logging levels used throughout the application.
    """

    NOTSET = "NOTSET"  # 0
    DEBUG = "DEBUG"  # 10
    INFO = "INFO"  # 20
    WARNING = "WARNING"  # 30
    ERROR = "ERROR"  # 40
    FATAL = "FATAL"  # 50


class AioSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="CONTEXTFORGE_CLI_CONFIG_",
        env_file=(".env", ".envrc"),
        env_file_encoding="utf-8",
        extra="allow",
        arbitrary_types_allowed=True,
        json_schema_extra={
            "properties": {
                "llm_retriever_type": {
                    "type": "string",
                    "default": "vector_store",
                    "description": "Type of retriever to use",
                }
            }
        },
    )


def get_rich_console() -> Console:
    """Get a Rich console instance for formatted output.

    Returns:
        Console: A configured Rich console instance for formatted terminal output
    """
    return Console()


# Global settings instance
aiosettings = AioSettings()
# avoid-global-variables
# In-place reloading
aiosettings.__init__()

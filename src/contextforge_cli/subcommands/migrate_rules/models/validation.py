"""Validation result models for MDC file validation.

This module defines the core models used for validation results and context
in the MDC file validation system. These models are used across all validators
to ensure consistent result formatting and context handling.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class ValidationSeverity(str, Enum):
    """Enumeration of possible validation result severities.

    Attributes:
        ERROR: Critical issues that must be fixed
        WARNING: Potential issues that should be reviewed
        INFO: Informational messages about the validation
    """

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationLocation(BaseModel):
    """Location information for validation results.

    Attributes:
        line: Line number in the file (1-based)
        column: Column number in the file (1-based)
        section: Section of the file (e.g., "frontmatter", "content")
        context: Surrounding context of the validation point
    """

    line: int | None = Field(None, ge=1, description="Line number (1-based)")
    column: int | None = Field(None, ge=1, description="Column number (1-based)")
    section: str = Field(..., description="Section of the file")
    context: str | None = Field(None, description="Surrounding context")

    def __str__(self) -> str:
        """Format location as a human-readable string.

        Returns:
            A formatted string describing the location
        """
        parts = [f"section: {self.section}"]
        if self.line is not None:
            parts.append(f"line: {self.line}")
        if self.column is not None:
            parts.append(f"column: {self.column}")
        return ", ".join(parts)


class ValidationResult(BaseModel):
    """Result of a single validation check.

    Attributes:
        is_valid: Whether the validation passed
        severity: Severity level of the result
        message: Human-readable description of the validation result
        location: Where in the file the validation was performed
        details: Additional structured information about the validation
        rule_id: Optional identifier of the validation rule
    """

    is_valid: bool = Field(..., description="Whether the validation passed")
    severity: ValidationSeverity = Field(
        default=ValidationSeverity.ERROR,
        description="Severity level of the validation result",
    )
    message: str = Field(..., description="Human-readable validation message")
    location: ValidationLocation | None = Field(
        None, description="Location information for the validation"
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured information",
    )
    rule_id: str | None = Field(None, description="Identifier of the validation rule")

    def __str__(self) -> str:
        """Format the validation result as a human-readable string.

        Returns:
            A formatted string describing the validation result
        """
        parts = [
            f"[{self.severity.value.upper()}] {'PASS' if self.is_valid else 'FAIL'}:",
            self.message,
        ]
        if self.location:
            parts.append(f"Location: {self.location}")
        if self.details:
            parts.append("Details:")
            for key, value in self.details.items():
                parts.append(f"  {key}: {value}")
        return "\n".join(parts)


class ValidationContext(BaseModel):
    """Context for validation operations.

    This model provides all necessary context for validators to perform their
    checks, including file information, content, and related resources.

    Attributes:
        workspace_root: Root directory of the workspace
        file_path: Path to the file being validated
        content: Content of the file
        related_files: Map of related file paths to their contents
        config: Optional configuration for validation
    """

    workspace_root: Path = Field(..., description="Root directory of the workspace")
    file_path: Path = Field(..., description="Path to the file being validated")
    content: str = Field(..., description="Content of the file")
    related_files: dict[Path, str] = Field(
        default_factory=dict,
        description="Map of related file paths to their contents",
    )
    config: dict[str, Any] | None = Field(
        None, description="Optional validation configuration"
    )

    @field_validator("workspace_root", "file_path", mode="before")
    @classmethod
    def ensure_absolute_path(cls, v: Any) -> Path:
        """Ensure paths are absolute and properly formatted.

        Args:
            v: The path value to validate

        Returns:
            Path: An absolute Path object

        Raises:
            ValueError: If the path is not absolute
        """
        if isinstance(v, str):
            v = Path(v)
        if not v.is_absolute():
            raise ValueError(f"Path must be absolute: {v}")
        return v

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: Path, values: dict[str, Any]) -> Path:
        """Validate that file_path is within workspace_root.

        Args:
            v: The file path to validate
            values: Previously validated values

        Returns:
            Path: The validated file path

        Raises:
            ValueError: If the file path is not within workspace_root
        """
        workspace_root = values.get("workspace_root")
        if workspace_root and not str(v).startswith(str(workspace_root)):
            raise ValueError(f"File path must be within workspace root: {v}")
        return v


class ValidationSummary(BaseModel):
    """Summary of all validation results for a file.

    Attributes:
        file_path: Path to the validated file
        is_valid: Whether all validations passed
        results: List of individual validation results
        error_count: Number of error severity results
        warning_count: Number of warning severity results
        info_count: Number of info severity results
    """

    file_path: Path = Field(..., description="Path to the validated file")
    is_valid: bool = Field(..., description="Whether all validations passed")
    results: Sequence[ValidationResult] = Field(
        ..., description="List of validation results"
    )
    error_count: int = Field(0, ge=0, description="Number of errors")
    warning_count: int = Field(0, ge=0, description="Number of warnings")
    info_count: int = Field(0, ge=0, description="Number of info messages")

    @field_validator("file_path", mode="before")
    @classmethod
    def ensure_absolute_path(cls, v: Any) -> Path:
        """Ensure file_path is absolute and properly formatted.

        Args:
            v: The path value to validate

        Returns:
            Path: An absolute Path object

        Raises:
            ValueError: If the path is not absolute
        """
        if isinstance(v, str):
            v = Path(v)
        if not v.is_absolute():
            raise ValueError(f"Path must be absolute: {v}")
        return v

    def __str__(self) -> str:
        """Format the validation summary as a human-readable string.

        Returns:
            A formatted string describing the validation summary
        """
        parts = [
            f"Validation Summary for {self.file_path}",
            f"Status: {'PASS' if self.is_valid else 'FAIL'}",
            f"Results: {len(self.results)} total",
            f"  - Errors: {self.error_count}",
            f"  - Warnings: {self.warning_count}",
            f"  - Info: {self.info_count}",
        ]
        if self.results:
            parts.append("\nDetailed Results:")
            for result in self.results:
                parts.extend(str(result).split("\n"))
        return "\n".join(parts)

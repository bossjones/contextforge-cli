"""Exception classes for MDC file validation.

This module defines a hierarchy of exceptions used in the MDC file validation system.
Each exception type corresponds to a specific validation failure category.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Dict, Optional


class ValidationError(Exception):
    """Base exception class for all validation errors.

    Attributes:
        message: A human-readable error message
        location: Where in the file the error occurred (e.g., "line 5", "frontmatter")
        details: Additional structured information about the error
        severity: The severity level of the error ("error", "warning", "info")
    """

    def __init__(
        self,
        message: str,
        *,
        location: str | None = None,
        details: dict[str, Any] | None = None,
        severity: str = "error",
    ) -> None:
        """Initialize a ValidationError.

        Args:
            message: A human-readable error message
            location: Where in the file the error occurred
            details: Additional structured information about the error
            severity: The severity level of the error
        """
        self.message = message
        self.location = location
        self.details = details or {}
        self.severity = severity
        super().__init__(self.format_message())

    def format_message(self) -> str:
        """Format the error message with location and details.

        Returns:
            A formatted error message string
        """
        parts = [self.message]
        if self.location:
            parts.append(f"Location: {self.location}")
        if self.details:
            parts.append("Details:")
            for key, value in self.details.items():
                parts.append(f"  {key}: {value}")
        return "\n".join(parts)


class FrontmatterError(ValidationError):
    """Exception raised for YAML frontmatter validation failures.

    This includes issues with:
    - Missing required fields
    - Invalid YAML syntax
    - Schema validation failures
    - Position requirements (must be at top)
    """

    def __init__(
        self,
        message: str,
        *,
        location: str | None = None,
        details: dict[str, Any] | None = None,
        missing_fields: Sequence[str] | None = None,
    ) -> None:
        """Initialize a FrontmatterError.

        Args:
            message: A human-readable error message
            location: Where in the frontmatter the error occurred
            details: Additional structured information about the error
            missing_fields: List of required fields that are missing
        """
        if missing_fields:
            details = details or {}
            details["missing_fields"] = missing_fields
        super().__init__(message, location=location, details=details)


class AnnotationError(ValidationError):
    """Exception raised for @annotation validation failures.

    This includes issues with:
    - Invalid JSON syntax in annotations
    - Missing required annotation sections
    - Schema validation failures for specific annotations
    """

    def __init__(
        self,
        message: str,
        *,
        location: str | None = None,
        details: dict[str, Any] | None = None,
        annotation_type: str | None = None,
    ) -> None:
        """Initialize an AnnotationError.

        Args:
            message: A human-readable error message
            location: Where in the file the error occurred
            details: Additional structured information about the error
            annotation_type: The type of annotation that failed validation
        """
        if annotation_type:
            details = details or {}
            details["annotation_type"] = annotation_type
        super().__init__(message, location=location, details=details)


class ContentError(ValidationError):
    """Exception raised for content structure validation failures.

    This includes issues with:
    - Heading hierarchy
    - Code block formatting
    - Required sections
    - Content organization
    """

    def __init__(
        self,
        message: str,
        *,
        location: str | None = None,
        details: dict[str, Any] | None = None,
        content_type: str | None = None,
    ) -> None:
        """Initialize a ContentError.

        Args:
            message: A human-readable error message
            location: Where in the file the error occurred
            details: Additional structured information about the error
            content_type: The type of content that failed validation
        """
        if content_type:
            details = details or {}
            details["content_type"] = content_type
        super().__init__(message, location=location, details=details)


class XMLTagError(ValidationError):
    """Exception raised for XML tag validation failures.

    This includes issues with:
    - Invalid tag structure
    - Missing required tags
    - Improper nesting
    - Tag attribute validation
    """

    def __init__(
        self,
        message: str,
        *,
        location: str | None = None,
        details: dict[str, Any] | None = None,
        tag_name: str | None = None,
        tag_path: str | None = None,
    ) -> None:
        """Initialize an XMLTagError.

        Args:
            message: A human-readable error message
            location: Where in the file the error occurred
            details: Additional structured information about the error
            tag_name: The name of the tag that failed validation
            tag_path: The full path to the tag in the XML structure
        """
        details = details or {}
        if tag_name:
            details["tag_name"] = tag_name
        if tag_path:
            details["tag_path"] = tag_path
        super().__init__(message, location=location, details=details)


class CrossRefError(ValidationError):
    """Exception raised for cross-reference validation failures.

    This includes issues with:
    - Missing referenced files
    - Invalid file paths
    - Broken internal references
    - Circular references
    """

    def __init__(
        self,
        message: str,
        *,
        location: str | None = None,
        details: dict[str, Any] | None = None,
        ref_type: str | None = None,
        ref_path: str | None = None,
    ) -> None:
        """Initialize a CrossRefError.

        Args:
            message: A human-readable error message
            location: Where in the file the error occurred
            details: Additional structured information about the error
            ref_type: The type of reference that failed validation
            ref_path: The path or identifier of the failed reference
        """
        details = details or {}
        if ref_type:
            details["ref_type"] = ref_type
        if ref_path:
            details["ref_path"] = ref_path
        super().__init__(message, location=location, details=details)

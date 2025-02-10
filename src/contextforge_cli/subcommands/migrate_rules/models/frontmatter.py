"""Frontmatter models for MDC file validation.

This module provides models for validating frontmatter in MDC files,
including schema definitions and validation rules.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field, field_validator


class FrontmatterMetadata(BaseModel):
    """Metadata fields for MDC file frontmatter.

    Attributes:
        title: Title of the document
        description: Brief description of the document
        author: Author of the document
        date: Creation or last modified date
        tags: List of tags for categorization
        version: Document version
        status: Document status (e.g., draft, review, final)
    """

    title: str = Field(..., description="Title of the document")
    description: str | None = Field(None, description="Brief description")
    author: str | None = Field(None, description="Document author")
    date: datetime | None = Field(None, description="Document date")
    tags: list[str] = Field(default_factory=list, description="Document tags")
    version: str | None = Field(None, description="Document version")
    status: str | None = Field(None, description="Document status")


class FrontmatterConfig(BaseModel):
    """Configuration for frontmatter validation.

    Attributes:
        required_fields: Fields that must be present
        optional_fields: Additional allowed fields
        allowed_statuses: Valid status values
        date_formats: Accepted date formats
        max_title_length: Maximum length for titles
        max_description_length: Maximum length for descriptions
    """

    required_fields: set[str] = Field(
        default={"title"},
        description="Required frontmatter fields",
    )
    optional_fields: set[str] = Field(
        default={
            "description",
            "author",
            "date",
            "tags",
            "version",
            "status",
        },
        description="Optional frontmatter fields",
    )
    allowed_statuses: set[str] = Field(
        default={
            "draft",
            "review",
            "final",
            "archived",
            "deprecated",
        },
        description="Valid status values",
    )
    date_formats: list[str] = Field(
        default=[
            "%Y-%m-%d",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
        ],
        description="Accepted date formats",
    )
    max_title_length: int = Field(
        default=100,
        description="Maximum title length",
    )
    max_description_length: int = Field(
        default=500,
        description="Maximum description length",
    )

    @field_validator("required_fields", "optional_fields", "allowed_statuses")
    @classmethod
    def validate_field_names(cls, v: set[str]) -> set[str]:
        """Validate field names are lowercase and valid.

        Args:
            v: Set of field names to validate

        Returns:
            Validated set of field names

        Raises:
            ValueError: If any field names are invalid
        """
        return {name.lower() for name in v}


class FrontmatterValidationResult(BaseModel):
    """Result of frontmatter validation.

    Attributes:
        is_valid: Whether the frontmatter is valid
        errors: List of validation errors
        warnings: List of validation warnings
        metadata: Parsed frontmatter metadata
    """

    is_valid: bool = Field(..., description="Whether validation passed")
    errors: list[str] = Field(
        default_factory=list,
        description="Validation errors",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Validation warnings",
    )
    metadata: FrontmatterMetadata | None = Field(
        None,
        description="Parsed frontmatter metadata",
    )

    def __str__(self) -> str:
        """Format the validation result as a human-readable string.

        Returns:
            A formatted string describing the validation result
        """
        parts = [f"Frontmatter validation: {'PASS' if self.is_valid else 'FAIL'}"]
        if self.errors:
            parts.append("\nErrors:")
            parts.extend(f"  - {error}" for error in self.errors)
        if self.warnings:
            parts.append("\nWarnings:")
            parts.extend(f"  - {warning}" for warning in self.warnings)
        if self.metadata:
            parts.append("\nMetadata:")
            for field, value in self.metadata.model_dump().items():
                if value is not None:
                    parts.append(f"  {field}: {value}")
        return "\n".join(parts)

"""Context models for MDC file validation.

This module provides the context models used during MDC file validation,
including file information, content, and validation state.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, field_validator

from contextforge_cli.subcommands.migrate_rules.models.validation import (
    ValidationLocation,
)


class MDCContext(BaseModel):
    """Context for MDC file validation.

    This model provides the context needed for validating MDC files,
    including file content, location information, and validation state.

    Attributes:
        content: The content of the MDC file
        file_path: Path to the file being validated
        validator_name: Name of the current validator
        line_number: Current line number being validated
        section: Current section being validated
        state: Additional validation state information
    """

    content: str = Field(..., description="Content of the MDC file")
    file_path: str = Field(..., description="Path to the file being validated")
    validator_name: str | None = Field(
        None, description="Name of the current validator"
    )
    line_number: int | None = Field(None, ge=1, description="Current line number")
    section: str | None = Field(None, description="Current section being validated")
    state: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional validation state information",
    )

    def with_location(self, location: ValidationLocation) -> MDCContext:
        """Create a new context with updated location information.

        Args:
            location: New location information to apply

        Returns:
            A new MDCContext instance with updated location
        """
        return self.model_copy(
            update={
                "line_number": location.line,
                "section": location.section,
                "validator_name": location.validator_name,
            }
        )

    def with_validator(self, validator_name: str) -> MDCContext:
        """Create a new context with a different validator name.

        Args:
            validator_name: Name of the validator to use

        Returns:
            A new MDCContext instance with updated validator name
        """
        return self.model_copy(update={"validator_name": validator_name})

    def with_section(self, section: str) -> MDCContext:
        """Create a new context for a different section.

        Args:
            section: Name of the section to validate

        Returns:
            A new MDCContext instance with updated section
        """
        return self.model_copy(update={"section": section})

    def with_state(self, **kwargs: Any) -> MDCContext:
        """Create a new context with updated state information.

        Args:
            **kwargs: State information to update

        Returns:
            A new MDCContext instance with updated state
        """
        new_state = self.state.copy()
        new_state.update(kwargs)
        return self.model_copy(update={"state": new_state})

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        """Validate and normalize the file path.

        Args:
            v: File path to validate

        Returns:
            Normalized file path as string

        Raises:
            ValueError: If the file path is invalid
        """
        try:
            path = Path(v)
            return str(path.resolve())
        except Exception as e:
            raise ValueError(f"Invalid file path: {e}")

    def __str__(self) -> str:
        """Format the context as a human-readable string.

        Returns:
            A formatted string describing the context
        """
        parts = [f"File: {self.file_path}"]
        if self.validator_name:
            parts.append(f"Validator: {self.validator_name}")
        if self.line_number:
            parts.append(f"Line: {self.line_number}")
        if self.section:
            parts.append(f"Section: {self.section}")
        if self.state:
            parts.append("State:")
            for key, value in self.state.items():
                parts.append(f"  {key}: {value}")
        return "\n".join(parts)

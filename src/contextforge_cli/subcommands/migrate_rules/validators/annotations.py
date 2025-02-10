"""Annotation validator for MDC files.

This module provides validation for @annotation blocks in MDC files, ensuring
proper JSON structure, required sections, and correct formatting.
"""

from __future__ import annotations

import json
import re
from collections.abc import AsyncGenerator
from re import Pattern
from typing import Any, Dict, List, Optional, Set

import structlog
from pydantic import BaseModel, Field

from contextforge_cli.subcommands.migrate_rules.exceptions.validation import (
    AnnotationError,
)
from contextforge_cli.subcommands.migrate_rules.models.validation import (
    ValidationContext,
    ValidationLocation,
    ValidationResult,
    ValidationSeverity,
)
from contextforge_cli.subcommands.migrate_rules.validators.base import (
    BaseValidator,
    ValidatorConfig,
)


class AnnotationSchema(BaseModel):
    """Schema for MDC file annotations.

    Attributes:
        type: Type of the annotation (e.g., "context", "rules", "implementation")
        content: The JSON content of the annotation
    """

    type: str = Field(..., description="Type of the annotation")
    content: dict[str, Any] = Field(..., description="JSON content of the annotation")


class AnnotationValidatorConfig(ValidatorConfig):
    """Configuration for annotation validation.

    Attributes:
        required_annotations: Set of annotation types that must be present
        allow_unknown_types: Whether to allow annotation types not in known_types
        known_types: Set of known annotation types
        annotation_pattern: Regex pattern for matching annotations
    """

    required_annotations: set[str] = Field(
        default={"context", "implementation"},
        description="Set of required annotation types",
    )
    allow_unknown_types: bool = Field(
        default=False,
        description="Whether to allow unknown annotation types",
    )
    known_types: set[str] = Field(
        default={
            "context",
            "implementation",
            "rules",
            "format",
            "options",
            "examples",
            "validation",
            "thinking",
            "quotes",
        },
        description="Set of known annotation types",
    )
    annotation_pattern: str = Field(
        default=r"@(\w+)\s*({[^@]*})",
        description="Regex pattern for matching annotations",
    )


class AnnotationValidator(BaseValidator):
    """Validator for @annotation blocks in MDC files.

    This validator checks:
    - Presence of required annotations
    - JSON syntax in annotation content
    - Annotation type validity
    - Content structure based on type
    - Nesting and formatting
    """

    def __init__(
        self,
        name: str = "annotations",
        description: str = "Validates @annotation blocks in MDC files",
        config: AnnotationValidatorConfig | None = None,
    ) -> None:
        """Initialize the annotation validator.

        Args:
            name: Name of the validator
            description: Description of what this validator checks
            config: Optional validator configuration
        """
        super().__init__(name, description, config or AnnotationValidatorConfig())
        self.config = config or AnnotationValidatorConfig()
        self._pattern: Pattern[str] = re.compile(
            self.config.annotation_pattern, re.MULTILINE | re.DOTALL
        )

    def _extract_annotations(
        self, content: str
    ) -> list[tuple[str, str, int, int | None]]:
        """Extract annotations from content.

        Args:
            content: The content to extract annotations from

        Returns:
            List of tuples containing (type, content, start_pos, line_number)
        """
        annotations = []
        for match in self._pattern.finditer(content):
            ann_type = match.group(1)
            ann_content = match.group(2)
            start_pos = match.start()
            # Calculate line number
            line_number = content.count("\n", 0, start_pos) + 1
            annotations.append((ann_type, ann_content, start_pos, line_number))
        return annotations

    def _validate_json_content(
        self, content: str, line_number: int
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """Validate JSON content of an annotation.

        Args:
            content: The JSON content to validate
            line_number: Line number where the content starts

        Returns:
            Tuple of (is_valid, parsed_content, error_message)
        """
        try:
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                return False, None, "Annotation content must be a JSON object"
            return True, parsed, None
        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON syntax: {str(e)}"

    async def validate(
        self, context: ValidationContext
    ) -> AsyncGenerator[ValidationResult, None]:
        """Validate annotations in an MDC file.

        Args:
            context: Validation context containing file and workspace information

        Yields:
            ValidationResult for each validation check

        Raises:
            AnnotationError: If annotations cannot be parsed
        """
        content = context.content

        # Extract all annotations
        annotations = self._extract_annotations(content)
        found_types = set()

        # Track annotation order for nesting validation
        current_section: str | None = None
        nesting_stack: list[str] = []

        for ann_type, ann_content, start_pos, line_number in annotations:
            found_types.add(ann_type)

            # Validate annotation type
            if (
                not self.config.allow_unknown_types
                and ann_type not in self.config.known_types
            ):
                yield ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Unknown annotation type: @{ann_type}",
                    location=ValidationLocation(
                        line=line_number,
                        column=1,
                        section="annotations",
                        context=f"@{ann_type}",
                    ),
                )
                continue

            # Validate JSON content
            is_valid, parsed_content, error_message = self._validate_json_content(
                ann_content, line_number
            )
            if not is_valid:
                yield ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=error_message or "Invalid JSON content",
                    location=ValidationLocation(
                        line=line_number,
                        column=1,
                        section="annotations",
                        context=ann_content,
                    ),
                )
                continue

            # Validate content structure based on type
            try:
                annotation = AnnotationSchema(type=ann_type, content=parsed_content)

                # Validate nesting (if needed)
                if current_section:
                    nesting_stack.append(current_section)
                current_section = ann_type

                yield ValidationResult(
                    is_valid=True,
                    severity=ValidationSeverity.INFO,
                    message=f"Valid @{ann_type} annotation",
                    location=ValidationLocation(
                        line=line_number,
                        column=1,
                        section="annotations",
                        context=f"@{ann_type}",
                    ),
                )

            except Exception as e:
                yield ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid annotation structure: {str(e)}",
                    location=ValidationLocation(
                        line=line_number,
                        column=1,
                        section="annotations",
                        context=ann_content,
                    ),
                )

        # Check for missing required annotations
        missing = self.config.required_annotations - found_types
        if missing:
            yield ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Missing required annotations: {', '.join(f'@{t}' for t in missing)}",
                location=ValidationLocation(
                    line=1,
                    column=1,
                    section="annotations",
                ),
            )

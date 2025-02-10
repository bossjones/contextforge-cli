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
from contextforge_cli.subcommands.migrate_rules.models.annotations import (
    ANNOTATION_TYPE_MAP,
    AnnotationContent,
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

logger = structlog.get_logger(__name__)


class AnnotationsConfig(ValidatorConfig):
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
        default_factory=lambda: set(ANNOTATION_TYPE_MAP.keys()),
        description="Set of known annotation types",
    )
    annotation_pattern: str = Field(
        default=r"@(\w+)\s*{([^}]*)}",
        description="Regex pattern for matching annotations",
    )


class AnnotationsValidator(BaseValidator):
    """Validator for MDC file annotations.

    This validator checks:
    1. Required annotations are present
    2. Annotation types are known/allowed
    3. JSON content is valid
    4. Content matches schema for each type
    """

    def __init__(
        self,
        name: str = "annotations",
        description: str = "Validates @annotation blocks in MDC files",
        config: AnnotationsConfig | None = None,
    ) -> None:
        """Initialize the AnnotationValidator.

        Args:
            name: Name of the validator
            description: Description of what this validator does
            config: Configuration for the validator
        """
        super().__init__(name, description, config or AnnotationsConfig())
        self.config = config or AnnotationsConfig()
        self._pattern: Pattern[str] = re.compile(self.config.annotation_pattern)

    def _extract_annotations(
        self, content: str
    ) -> list[tuple[str, str, int, int | None]]:
        """Extract annotations from content.

        Args:
            content: The content to extract annotations from

        Returns:
            List of tuples containing (type, content, start_line, end_line)
        """
        annotations: list[tuple[str, str, int, int | None]] = []
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            matches = self._pattern.finditer(line)
            for match in matches:
                ann_type = match.group(1)
                ann_content = match.group(2).strip()
                annotations.append((ann_type, ann_content, i, None))

        return annotations

    def _validate_json_content(
        self, content: str, line_number: int
    ) -> tuple[bool, dict[str, Any] | None, str | None]:
        """Validate JSON content of an annotation.

        Args:
            content: The JSON content to validate
            line_number: Line number where the content appears

        Returns:
            Tuple of (is_valid, parsed_content, error_message)
        """
        try:
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                return False, None, "Annotation content must be a JSON object"
            return True, parsed, None
        except json.JSONDecodeError as e:
            return False, None, f"Invalid JSON: {str(e)}"

    async def validate(
        self, context: ValidationContext
    ) -> AsyncGenerator[ValidationResult, None]:
        """Validate annotations in the given context.

        Args:
            context: The validation context containing the content to validate

        Yields:
            ValidationResult objects for each validation issue found
        """
        found_types: set[str] = set()
        annotations = self._extract_annotations(context.content)

        # Check each annotation
        for ann_type, content, line_number, _ in annotations:
            # Check if type is known/allowed
            if (
                ann_type not in self.config.known_types
                and not self.config.allow_unknown_types
            ):
                yield ValidationResult(
                    message=f"Unknown annotation type: {ann_type}",
                    line_number=line_number,
                    severity=ValidationSeverity.ERROR,
                    context=context.with_location(
                        ValidationLocation(
                            line_number=line_number,
                            validator_name=self.name,
                        )
                    ),
                )
                continue

            found_types.add(ann_type)

            # Validate JSON content
            is_valid, parsed_content, error_msg = self._validate_json_content(
                content, line_number
            )
            if not is_valid:
                yield ValidationResult(
                    message=f"Invalid annotation content: {error_msg}",
                    line_number=line_number,
                    severity=ValidationSeverity.ERROR,
                    context=context.with_location(
                        ValidationLocation(
                            line_number=line_number,
                            validator_name=self.name,
                        )
                    ),
                )
                continue

            # Validate against schema
            try:
                if ann_type in ANNOTATION_TYPE_MAP:
                    model_class = ANNOTATION_TYPE_MAP[ann_type]
                    model_class(type=ann_type, **parsed_content)
            except Exception as e:
                yield ValidationResult(
                    message=f"Schema validation failed: {str(e)}",
                    line_number=line_number,
                    severity=ValidationSeverity.ERROR,
                    context=context.with_location(
                        ValidationLocation(
                            line_number=line_number,
                            validator_name=self.name,
                        )
                    ),
                )

        # Check for missing required annotations
        missing = self.config.required_annotations - found_types
        if missing:
            yield ValidationResult(
                message=f"Missing required annotations: {', '.join(missing)}",
                line_number=1,
                severity=ValidationSeverity.ERROR,
                context=context.with_location(
                    ValidationLocation(
                        line_number=1,
                        validator_name=self.name,
                    )
                ),
            )

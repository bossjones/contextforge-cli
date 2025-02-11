"""YAML frontmatter validator for MDC files.

This module provides validation for YAML frontmatter in MDC files, ensuring
proper structure, required fields, and correct positioning.
"""

from __future__ import annotations

import re
from collections.abc import AsyncGenerator
from typing import Any, Dict, List, Optional, Set

import structlog
import yaml
from pydantic import BaseModel, Field

from contextforge_cli.subcommands.migrate_rules.exceptions.validation import (
    FrontmatterError,
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


class FrontmatterSchema(BaseModel):
    """Schema for MDC file frontmatter.

    Attributes:
        description: Single sentence description of the file's purpose
        globs: Array of file patterns this MDC applies to
        related_docs: Optional array of related documentation files
    """

    description: str = Field(..., description="Single sentence description")
    globs: list[str] = Field(..., description="Array of file patterns")
    related_docs: list[str] | None = Field(
        None, description="Optional array of related documentation files"
    )


class FrontmatterConfig(ValidatorConfig):
    """Configuration for frontmatter validation.

    Attributes:
        required_fields: Set of field names that must be present
        allow_extra_fields: Whether to allow fields not in schema
        max_description_length: Maximum length for description field
        custom_schema: Optional custom schema to use instead of default
    """

    required_fields: set[str] = Field(
        default={"description", "globs"},
        description="Set of required field names",
    )
    allow_extra_fields: bool = Field(
        default=False,
        description="Whether to allow fields not in schema",
    )
    max_description_length: int = Field(
        default=100,
        ge=1,
        description="Maximum length for description field",
    )
    custom_schema: dict[str, Any] | None = Field(
        None,
        description="Optional custom schema to use",
    )


class FrontmatterValidator(BaseValidator):
    """Validator for YAML frontmatter in MDC files.

    This validator checks:
    - Presence and position of frontmatter
    - YAML syntax
    - Required fields
    - Field types and constraints
    - Description format and length
    - File reference validity
    """

    def __init__(
        self,
        name: str = "frontmatter",
        description: str = "Validates YAML frontmatter in MDC files",
        config: FrontmatterConfig | None = None,
    ) -> None:
        """Initialize the frontmatter validator.

        Args:
            name: Name of the validator
            description: Description of what this validator checks
            config: Optional validator configuration
        """
        super().__init__(name, description, config or FrontmatterConfig())
        self.config = config or FrontmatterConfig()

    async def validate(
        self, context: ValidationContext
    ) -> AsyncGenerator[ValidationResult, None]:
        """Validate frontmatter in an MDC file.

        Args:
            context: Validation context containing file and workspace information

        Yields:
            ValidationResult for each validation check

        Raises:
            FrontmatterError: If frontmatter cannot be parsed
        """
        content = context.content.strip()

        # Check if frontmatter exists and is at the start
        if not content.startswith("---"):
            yield ValidationResult(
                message="Frontmatter must be at the start of the file and begin with '---'",
                line_number=1,
                severity=ValidationSeverity.ERROR,
                context=context.with_location(
                    ValidationLocation(
                        line_number=1,
                        validator_name=self.name,
                    )
                ),
            )
            return

        # Extract frontmatter content
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        if not match:
            yield ValidationResult(
                message="Invalid frontmatter format. Must be enclosed in '---'",
                line_number=1,
                severity=ValidationSeverity.ERROR,
                context=context.with_location(
                    ValidationLocation(
                        line_number=1,
                        validator_name=self.name,
                    )
                ),
            )
            return

        frontmatter_content = match.group(1)
        try:
            # Parse YAML content
            data = yaml.safe_load(frontmatter_content)
            if not isinstance(data, dict):
                yield ValidationResult(
                    message="Frontmatter must be a YAML dictionary",
                    line_number=1,
                    severity=ValidationSeverity.ERROR,
                    context=context.with_location(
                        ValidationLocation(
                            line_number=1,
                            validator_name=self.name,
                        )
                    ),
                )
                return

            # Validate against schema
            try:
                if self.config.custom_schema:
                    # TODO: Implement custom schema validation
                    pass
                else:
                    frontmatter = FrontmatterSchema(**data)

                    # Validate description
                    if (
                        len(frontmatter.description)
                        > self.config.max_description_length
                    ):
                        yield ValidationResult(
                            message=f"Description exceeds maximum length of {self.config.max_description_length} characters",
                            line_number=1,
                            severity=ValidationSeverity.ERROR,
                            context=context.with_location(
                                ValidationLocation(
                                    line_number=1,
                                    validator_name=self.name,
                                )
                            ),
                        )

                    # Validate globs
                    if not frontmatter.globs:
                        yield ValidationResult(
                            message="At least one glob pattern is required",
                            line_number=1,
                            severity=ValidationSeverity.ERROR,
                            context=context.with_location(
                                ValidationLocation(
                                    line_number=1,
                                    validator_name=self.name,
                                )
                            ),
                        )

                    # Validate related_docs if present
                    if frontmatter.related_docs:
                        for doc in frontmatter.related_docs:
                            if not (context.workspace_root / doc).exists():
                                yield ValidationResult(
                                    message=f"Referenced document does not exist: {doc}",
                                    line_number=1,
                                    severity=ValidationSeverity.ERROR,
                                    context=context.with_location(
                                        ValidationLocation(
                                            line_number=1,
                                            validator_name=self.name,
                                        )
                                    ),
                                )

            except Exception as e:
                yield ValidationResult(
                    message=f"Schema validation failed: {str(e)}",
                    line_number=1,
                    severity=ValidationSeverity.ERROR,
                    context=context.with_location(
                        ValidationLocation(
                            line_number=1,
                            validator_name=self.name,
                        )
                    ),
                )

        except yaml.YAMLError as e:
            yield ValidationResult(
                message=f"Invalid YAML syntax: {str(e)}",
                line_number=1,
                severity=ValidationSeverity.ERROR,
                context=context.with_location(
                    ValidationLocation(
                        line_number=1,
                        validator_name=self.name,
                    )
                ),
            )

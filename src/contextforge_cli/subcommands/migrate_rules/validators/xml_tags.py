"""XMLTagValidator for validating XML tags in MDC files.

This module provides validation for XML tags within MDC files, ensuring proper structure,
nesting, and attribute usage.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set
from xml.etree import ElementTree as ET

from pydantic import BaseModel, Field

from contextforge_cli.subcommands.migrate_rules.models.validation import (
    ValidationContext,
    ValidationResult,
    ValidationSeverity,
)
from contextforge_cli.subcommands.migrate_rules.validators.base import BaseValidator

if TYPE_CHECKING:
    from contextforge_cli.subcommands.migrate_rules.models.context import MDCContext


class XMLTagConfig(BaseModel):
    """Configuration for XML tag validation.

    Attributes:
        required_tags: Set of XML tags that must be present in the document
        allowed_tags: Set of XML tags that are allowed in the document
        required_attributes: Dict mapping tags to their required attributes
        allowed_attributes: Dict mapping tags to their allowed attributes
        max_nesting_depth: Maximum allowed nesting depth for XML tags
        validate_xml_syntax: Whether to validate XML syntax strictly
    """

    required_tags: set[str] = Field(default_factory=set)
    allowed_tags: set[str] = Field(default_factory=set)
    required_attributes: dict[str, set[str]] = Field(default_factory=dict)
    allowed_attributes: dict[str, set[str]] = Field(default_factory=dict)
    max_nesting_depth: int = Field(default=10)
    validate_xml_syntax: bool = Field(default=True)


class XMLTagValidator(BaseValidator):
    """Validator for XML tags in MDC files.

    This validator ensures that XML tags in MDC files follow proper structure,
    nesting rules, and attribute usage guidelines.
    """

    def __init__(self, config: XMLTagConfig | None = None) -> None:
        """Initialize the XMLTagValidator.

        Args:
            config: Configuration for XML tag validation. If None, default config is used.
        """
        super().__init__()
        self.config = config or XMLTagConfig()

    async def validate(self, context: MDCContext) -> list[ValidationResult]:
        """Validate XML tags in the MDC file.

        Args:
            context: The MDC context containing the file content and metadata.

        Returns:
            List of ValidationResult objects containing validation findings.
        """
        results: list[ValidationResult] = []
        content = context.content

        # Extract all XML-like tags from the content
        tag_pattern = r"<[^>]+>"
        xml_tags = re.finditer(tag_pattern, content)

        # Track tag occurrences and nesting
        tag_stack: list[str] = []
        found_tags: set[str] = set()
        current_line = 1

        for match in xml_tags:
            tag_text = match.group()
            line_number = content.count("\n", 0, match.start()) + 1

            # Skip tags in code blocks
            if self._is_in_code_block(content, match.start()):
                continue

            try:
                # Parse the tag
                if tag_text.startswith("</"):
                    # Closing tag
                    tag_name = tag_text[2:-1].split()[0]
                    if tag_stack and tag_stack[-1] == tag_name:
                        tag_stack.pop()
                    else:
                        results.append(
                            ValidationResult(
                                message=f"Mismatched closing tag: {tag_text}",
                                line_number=line_number,
                                severity=ValidationSeverity.ERROR,
                                context=ValidationContext(
                                    file_path=context.file_path,
                                    line=content.split("\n")[line_number - 1],
                                    validator_name=self.__class__.__name__,
                                ),
                            )
                        )
                else:
                    # Opening tag
                    tag_name = tag_text[1:-1].split()[0].rstrip("/")
                    found_tags.add(tag_name)

                    if not tag_text.endswith("/>"):
                        tag_stack.append(tag_name)

                    # Validate tag name
                    if (
                        self.config.allowed_tags
                        and tag_name not in self.config.allowed_tags
                    ):
                        results.append(
                            ValidationResult(
                                message=f"Unauthorized XML tag: {tag_name}",
                                line_number=line_number,
                                severity=ValidationSeverity.ERROR,
                                context=ValidationContext(
                                    file_path=context.file_path,
                                    line=content.split("\n")[line_number - 1],
                                    validator_name=self.__class__.__name__,
                                ),
                            )
                        )

                    # Validate nesting depth
                    if len(tag_stack) > self.config.max_nesting_depth:
                        results.append(
                            ValidationResult(
                                message=f"XML tag nesting too deep (max: {self.config.max_nesting_depth})",
                                line_number=line_number,
                                severity=ValidationSeverity.WARNING,
                                context=ValidationContext(
                                    file_path=context.file_path,
                                    line=content.split("\n")[line_number - 1],
                                    validator_name=self.__class__.__name__,
                                ),
                            )
                        )

                    # Validate attributes
                    if (
                        self.config.required_attributes
                        or self.config.allowed_attributes
                    ):
                        await self._validate_attributes(
                            tag_text, tag_name, line_number, content, context, results
                        )

            except Exception as e:
                results.append(
                    ValidationResult(
                        message=f"Invalid XML tag syntax: {str(e)}",
                        line_number=line_number,
                        severity=ValidationSeverity.ERROR,
                        context=ValidationContext(
                            file_path=context.file_path,
                            line=content.split("\n")[line_number - 1],
                            validator_name=self.__class__.__name__,
                        ),
                    )
                )

        # Check for unclosed tags
        if tag_stack:
            results.append(
                ValidationResult(
                    message=f"Unclosed XML tags: {', '.join(tag_stack)}",
                    line_number=current_line,
                    severity=ValidationSeverity.ERROR,
                    context=ValidationContext(
                        file_path=context.file_path,
                        line="",  # No specific line for this error
                        validator_name=self.__class__.__name__,
                    ),
                )
            )

        # Check for required tags
        missing_tags = self.config.required_tags - found_tags
        if missing_tags:
            results.append(
                ValidationResult(
                    message=f"Missing required XML tags: {', '.join(missing_tags)}",
                    line_number=1,  # Global error
                    severity=ValidationSeverity.ERROR,
                    context=ValidationContext(
                        file_path=context.file_path,
                        line="",  # No specific line for this error
                        validator_name=self.__class__.__name__,
                    ),
                )
            )

        return results

    async def _validate_attributes(
        self,
        tag_text: str,
        tag_name: str,
        line_number: int,
        content: str,
        context: MDCContext,
        results: list[ValidationResult],
    ) -> None:
        """Validate attributes of an XML tag.

        Args:
            tag_text: The full text of the XML tag
            tag_name: The name of the XML tag
            line_number: The line number where the tag appears
            content: The full content of the file
            context: The MDC context
            results: List to append validation results to
        """
        # Extract attributes
        attr_pattern = r'(\w+)=["\'](.*?)["\']'
        found_attrs = {match[0] for match in re.findall(attr_pattern, tag_text)}

        # Check required attributes
        if tag_name in self.config.required_attributes:
            missing_attrs = self.config.required_attributes[tag_name] - found_attrs
            if missing_attrs:
                results.append(
                    ValidationResult(
                        message=f"Missing required attributes for tag {tag_name}: {', '.join(missing_attrs)}",
                        line_number=line_number,
                        severity=ValidationSeverity.ERROR,
                        context=ValidationContext(
                            file_path=context.file_path,
                            line=content.split("\n")[line_number - 1],
                            validator_name=self.__class__.__name__,
                        ),
                    )
                )

        # Check allowed attributes
        if tag_name in self.config.allowed_attributes:
            invalid_attrs = found_attrs - self.config.allowed_attributes[tag_name]
            if invalid_attrs:
                results.append(
                    ValidationResult(
                        message=f"Invalid attributes for tag {tag_name}: {', '.join(invalid_attrs)}",
                        line_number=line_number,
                        severity=ValidationSeverity.ERROR,
                        context=ValidationContext(
                            file_path=context.file_path,
                            line=content.split("\n")[line_number - 1],
                            validator_name=self.__class__.__name__,
                        ),
                    )
                )

    def _is_in_code_block(self, content: str, position: int) -> bool:
        """Check if a position in the content is within a code block.

        Args:
            content: The full content of the file
            position: The position to check

        Returns:
            bool: True if the position is within a code block, False otherwise
        """
        lines = content[:position].split("\n")
        code_block_count = 0

        for line in lines:
            if line.strip().startswith("```"):
                code_block_count += 1

        return code_block_count % 2 == 1  # Odd number means we're inside a code block

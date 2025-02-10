"""Content structure validator for MDC files.

This module provides validation for markdown content structure in MDC files,
ensuring proper heading hierarchy, code block formatting, and section organization.
"""

from __future__ import annotations

import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from re import Pattern
from typing import Any, Dict, List, Optional, Set, Tuple

import structlog
from pydantic import BaseModel, Field

from ..exceptions.validation import ContentError
from ..models.validation import (
    ValidationContext,
    ValidationLocation,
    ValidationResult,
    ValidationSeverity,
)
from .base import BaseValidator, ValidatorConfig


@dataclass
class HeadingInfo:
    """Information about a markdown heading.

    Attributes:
        level: The heading level (1-6)
        text: The heading text
        line_number: Line number where the heading appears
    """

    level: int
    text: str
    line_number: int


class CodeBlockInfo(BaseModel):
    """Information about a code block.

    Attributes:
        language: The language specified for the block
        content: The content of the code block
        start_line: Starting line number
        end_line: Ending line number
        indentation: Block's indentation level
    """

    language: str | None = Field(None, description="Language specified for the block")
    content: str = Field(..., description="Content of the code block")
    start_line: int = Field(..., description="Starting line number")
    end_line: int = Field(..., description="Ending line number")
    indentation: int = Field(0, description="Block's indentation level")


class ContentValidatorConfig(ValidatorConfig):
    """Configuration for content structure validation.

    Attributes:
        max_heading_level: Maximum allowed heading level
        required_sections: Set of required section headings
        code_block_languages: Set of allowed code block languages
        require_language_spec: Whether code blocks must specify a language
        allow_raw_html: Whether raw HTML is allowed
        max_consecutive_blank_lines: Maximum allowed consecutive blank lines
    """

    max_heading_level: int = Field(
        default=4,
        ge=1,
        le=6,
        description="Maximum allowed heading level",
    )
    required_sections: set[str] = Field(
        default={"Purpose", "Implementation"},
        description="Set of required section headings",
    )
    code_block_languages: set[str] = Field(
        default={
            "python",
            "json",
            "yaml",
            "markdown",
            "bash",
            "xml",
            "typescript",
            "javascript",
        },
        description="Set of allowed code block languages",
    )
    require_language_spec: bool = Field(
        default=True,
        description="Whether code blocks must specify a language",
    )
    allow_raw_html: bool = Field(
        default=False,
        description="Whether raw HTML is allowed",
    )
    max_consecutive_blank_lines: int = Field(
        default=2,
        ge=1,
        description="Maximum allowed consecutive blank lines",
    )


class ContentValidator(BaseValidator):
    """Validator for markdown content structure in MDC files.

    This validator checks:
    - Heading hierarchy and nesting
    - Code block formatting and languages
    - Section organization and completeness
    - Spacing and formatting rules
    """

    def __init__(
        self,
        name: str = "content",
        description: str = "Validates markdown content structure in MDC files",
        config: ContentValidatorConfig | None = None,
    ) -> None:
        """Initialize the content validator.

        Args:
            name: Name of the validator
            description: Description of what this validator checks
            config: Optional validator configuration
        """
        super().__init__(name, description, config or ContentValidatorConfig())
        self.config = config or ContentValidatorConfig()
        self._heading_pattern: Pattern[str] = re.compile(r"^(#{1,6})\s+(.+)$")
        self._code_block_start: Pattern[str] = re.compile(r"^(`{3,}|~{3,})([\w-]+)?$")
        self._code_block_end: Pattern[str] = re.compile(r"^(`{3,}|~{3,})$")
        self._html_pattern: Pattern[str] = re.compile(r"<[^>]+>")

    def _extract_headings(self, content: str) -> list[HeadingInfo]:
        """Extract all headings from content.

        Args:
            content: The content to extract headings from

        Returns:
            List of HeadingInfo objects
        """
        headings = []
        for line_number, line in enumerate(content.split("\n"), 1):
            match = self._heading_pattern.match(line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headings.append(HeadingInfo(level, text, line_number))
        return headings

    def _extract_code_blocks(self, content: str) -> list[CodeBlockInfo]:
        """Extract all code blocks from content.

        Args:
            content: The content to extract code blocks from

        Returns:
            List of CodeBlockInfo objects
        """
        blocks = []
        lines = content.split("\n")
        in_block = False
        current_block: dict[str, Any] = {}

        for line_number, line in enumerate(lines, 1):
            stripped = line.strip()
            if not in_block:
                start_match = self._code_block_start.match(stripped)
                if start_match:
                    in_block = True
                    current_block = {
                        "start_line": line_number,
                        "language": start_match.group(2),
                        "content": [],
                        "indentation": len(line) - len(stripped),
                    }
            else:
                if self._code_block_end.match(stripped):
                    in_block["end_line"] = line_number
                    in_block["content"] = "\n".join(current_block["content"])
                    blocks.append(CodeBlockInfo(**current_block))
                    in_block = False
                    current_block = {}
                else:
                    current_block["content"].append(line)
        return blocks

    def _validate_heading_hierarchy(
        self, headings: list[HeadingInfo]
    ) -> AsyncGenerator[ValidationResult, None]:
        """Validate heading hierarchy.

        Args:
            headings: List of headings to validate

        Yields:
            ValidationResult for each validation check
        """
        if not headings:
            yield ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="No headings found in content",
                location=ValidationLocation(line=1, column=1, section="content"),
            )
            return

        prev_level = 0
        for heading in headings:
            # Check max level
            if heading.level > self.config.max_heading_level:
                yield ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Heading level {heading.level} exceeds maximum allowed level {self.config.max_heading_level}",
                    location=ValidationLocation(
                        line=heading.line_number,
                        column=1,
                        section="content",
                        context=f"{'#' * heading.level} {heading.text}",
                    ),
                )

            # Check hierarchy (can't skip levels)
            if heading.level > prev_level + 1 and prev_level > 0:
                yield ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message=f"Invalid heading hierarchy: H{prev_level} followed by H{heading.level}",
                    location=ValidationLocation(
                        line=heading.line_number,
                        column=1,
                        section="content",
                        context=f"{'#' * heading.level} {heading.text}",
                    ),
                )

            prev_level = heading.level

        # Check required sections
        found_sections = {h.text for h in headings}
        missing = self.config.required_sections - found_sections
        if missing:
            yield ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message=f"Missing required sections: {', '.join(missing)}",
                location=ValidationLocation(line=1, column=1, section="content"),
            )

    def _validate_code_blocks(
        self, blocks: list[CodeBlockInfo]
    ) -> AsyncGenerator[ValidationResult, None]:
        """Validate code blocks.

        Args:
            blocks: List of code blocks to validate

        Yields:
            ValidationResult for each validation check
        """
        for block in blocks:
            # Check language specification
            if self.config.require_language_spec and not block.language:
                yield ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.ERROR,
                    message="Code block must specify a language",
                    location=ValidationLocation(
                        line=block.start_line,
                        column=1,
                        section="content",
                        context="```",
                    ),
                )
            elif (
                block.language
                and block.language not in self.config.code_block_languages
            ):
                yield ValidationResult(
                    is_valid=False,
                    severity=ValidationSeverity.WARNING,
                    message=f"Unknown code block language: {block.language}",
                    location=ValidationLocation(
                        line=block.start_line,
                        column=1,
                        section="content",
                        context=f"```{block.language}",
                    ),
                )

            # Check indentation consistency
            if block.content:
                lines = block.content.split("\n")
                base_indent = block.indentation
                for i, line in enumerate(lines, block.start_line + 1):
                    if line.strip() and len(line) - len(line.lstrip()) < base_indent:
                        yield ValidationResult(
                            is_valid=False,
                            severity=ValidationSeverity.WARNING,
                            message="Inconsistent code block indentation",
                            location=ValidationLocation(
                                line=i,
                                column=1,
                                section="content",
                                context=line,
                            ),
                        )

    async def validate(
        self, context: ValidationContext
    ) -> AsyncGenerator[ValidationResult, None]:
        """Validate content structure in an MDC file.

        Args:
            context: Validation context containing file and workspace information

        Yields:
            ValidationResult for each validation check

        Raises:
            ContentError: If content cannot be parsed
        """
        content = context.content

        # Extract and validate headings
        headings = self._extract_headings(content)
        async for result in self._validate_heading_hierarchy(headings):
            yield result

        # Extract and validate code blocks
        code_blocks = self._extract_code_blocks(content)
        async for result in self._validate_code_blocks(code_blocks):
            yield result

        # Check for raw HTML if not allowed
        if not self.config.allow_raw_html and self._html_pattern.search(content):
            yield ValidationResult(
                is_valid=False,
                severity=ValidationSeverity.ERROR,
                message="Raw HTML is not allowed",
                location=ValidationLocation(line=1, column=1, section="content"),
            )

        # Check consecutive blank lines
        lines = content.split("\n")
        blank_count = 0
        for i, line in enumerate(lines, 1):
            if not line.strip():
                blank_count += 1
                if blank_count > self.config.max_consecutive_blank_lines:
                    yield ValidationResult(
                        is_valid=False,
                        severity=ValidationSeverity.WARNING,
                        message=f"Too many consecutive blank lines (max: {self.config.max_consecutive_blank_lines})",
                        location=ValidationLocation(
                            line=i,
                            column=1,
                            section="content",
                        ),
                    )
            else:
                blank_count = 0

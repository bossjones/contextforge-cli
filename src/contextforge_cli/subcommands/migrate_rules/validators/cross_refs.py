"""CrossRefValidator for validating cross-references in MDC files.

This module provides validation for cross-references between MDC files,
ensuring proper linking and reference integrity.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Set
from urllib.parse import unquote, urlparse

from pydantic import BaseModel, Field

from ..models.validation import (
    ValidationContext,
    ValidationResult,
    ValidationSeverity,
)
from .base import BaseValidator

if TYPE_CHECKING:
    from ..models.context import MDCContext


class CrossRefConfig(BaseModel):
    """Configuration for cross-reference validation.

    Attributes:
        allowed_extensions: Set of allowed file extensions for references
        validate_external_urls: Whether to validate external URLs
        require_relative_paths: Whether to require relative paths for internal references
        allow_anchor_only_refs: Whether to allow anchor-only references
        validate_anchors: Whether to validate anchor references
        base_path: Base path for resolving relative references
        ignored_urls: Set of URLs to ignore during validation
        required_ref_prefixes: Set of required prefixes for references
        max_reference_depth: Maximum depth for nested references
    """

    allowed_extensions: set[str] = Field(default_factory=lambda: {".md", ".mdc"})
    validate_external_urls: bool = Field(default=True)
    require_relative_paths: bool = Field(default=True)
    allow_anchor_only_refs: bool = Field(default=True)
    validate_anchors: bool = Field(default=True)
    base_path: Path | None = None
    ignored_urls: set[str] = Field(default_factory=set)
    required_ref_prefixes: set[str] = Field(default_factory=set)
    max_reference_depth: int = Field(default=5)


class CrossRefValidator(BaseValidator):
    """Validator for cross-references in MDC files.

    This validator ensures that cross-references between MDC files are valid,
    including checking file existence, anchor validity, and URL formatting.
    """

    def __init__(self, config: CrossRefConfig | None = None) -> None:
        """Initialize the CrossRefValidator.

        Args:
            config: Configuration for cross-reference validation. If None, default config is used.
        """
        super().__init__()
        self.config = config or CrossRefConfig()
        self._anchor_cache: dict[str, set[str]] = {}

    async def validate(self, context: MDCContext) -> list[ValidationResult]:
        """Validate cross-references in the MDC file.

        Args:
            context: The MDC context containing the file content and metadata.

        Returns:
            List of ValidationResult objects containing validation findings.
        """
        results: list[ValidationResult] = []
        content = context.content

        # Find all markdown links and references
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        ref_pattern = r"\[([^\]]+)\]:\s*(\S+)"

        # Track processed references to avoid duplicates
        processed_refs: set[str] = set()

        # Validate inline links
        for match in re.finditer(link_pattern, content):
            link_text, url = match.groups()
            line_number = content.count("\n", 0, match.start()) + 1

            # Skip if in code block
            if self._is_in_code_block(content, match.start()):
                continue

            # Skip if already processed
            if url in processed_refs:
                continue

            processed_refs.add(url)

            # Validate the reference
            result = await self._validate_reference(url, line_number, content, context)
            if result:
                results.append(result)

        # Validate reference-style links
        for match in re.finditer(ref_pattern, content):
            ref_text, url = match.groups()
            line_number = content.count("\n", 0, match.start()) + 1

            # Skip if in code block
            if self._is_in_code_block(content, match.start()):
                continue

            # Skip if already processed
            if url in processed_refs:
                continue

            processed_refs.add(url)

            # Validate the reference
            result = await self._validate_reference(url, line_number, content, context)
            if result:
                results.append(result)

        return results

    async def _validate_reference(
        self,
        url: str,
        line_number: int,
        content: str,
        context: MDCContext,
    ) -> ValidationResult | None:
        """Validate a single reference.

        Args:
            url: The URL or reference to validate
            line_number: The line number where the reference appears
            content: The full content of the file
            context: The MDC context

        Returns:
            Optional[ValidationResult]: Validation result if there's an issue, None otherwise
        """
        # Clean the URL
        url = url.strip()
        if not url:
            return ValidationResult(
                message="Empty reference URL",
                line_number=line_number,
                severity=ValidationSeverity.ERROR,
                context=ValidationContext(
                    file_path=context.file_path,
                    line=content.split("\n")[line_number - 1],
                    validator_name=self.__class__.__name__,
                ),
            )

        # Check if URL should be ignored
        if url in self.config.ignored_urls:
            return None

        # Parse the URL
        parsed = urlparse(url)

        # Handle anchor-only references
        if url.startswith("#"):
            if not self.config.allow_anchor_only_refs:
                return ValidationResult(
                    message="Anchor-only references are not allowed",
                    line_number=line_number,
                    severity=ValidationSeverity.ERROR,
                    context=ValidationContext(
                        file_path=context.file_path,
                        line=content.split("\n")[line_number - 1],
                        validator_name=self.__class__.__name__,
                    ),
                )
            if self.config.validate_anchors:
                return await self._validate_anchor(
                    url[1:], line_number, content, context
                )
            return None

        # Validate external URLs
        if parsed.scheme in ("http", "https"):
            if not self.config.validate_external_urls:
                return None
            # Here you might want to add actual URL validation logic
            # For now, we just check basic structure
            if not all([parsed.scheme, parsed.netloc]):
                return ValidationResult(
                    message=f"Invalid external URL: {url}",
                    line_number=line_number,
                    severity=ValidationSeverity.ERROR,
                    context=ValidationContext(
                        file_path=context.file_path,
                        line=content.split("\n")[line_number - 1],
                        validator_name=self.__class__.__name__,
                    ),
                )
            return None

        # Handle internal references
        if self.config.require_relative_paths and url.startswith("/"):
            return ValidationResult(
                message="Absolute paths are not allowed for internal references",
                line_number=line_number,
                severity=ValidationSeverity.ERROR,
                context=ValidationContext(
                    file_path=context.file_path,
                    line=content.split("\n")[line_number - 1],
                    validator_name=self.__class__.__name__,
                ),
            )

        # Validate file extension
        file_path = Path(unquote(parsed.path))
        if file_path.suffix and file_path.suffix not in self.config.allowed_extensions:
            return ValidationResult(
                message=f"Invalid file extension: {file_path.suffix}",
                line_number=line_number,
                severity=ValidationSeverity.ERROR,
                context=ValidationContext(
                    file_path=context.file_path,
                    line=content.split("\n")[line_number - 1],
                    validator_name=self.__class__.__name__,
                ),
            )

        # Validate reference prefix
        if self.config.required_ref_prefixes:
            if not any(
                url.startswith(prefix) for prefix in self.config.required_ref_prefixes
            ):
                return ValidationResult(
                    message="Reference does not start with required prefix",
                    line_number=line_number,
                    severity=ValidationSeverity.ERROR,
                    context=ValidationContext(
                        file_path=context.file_path,
                        line=content.split("\n")[line_number - 1],
                        validator_name=self.__class__.__name__,
                    ),
                )

        # Validate file existence
        if self.config.base_path:
            full_path = self.config.base_path / file_path
            if not full_path.exists():
                return ValidationResult(
                    message=f"Referenced file does not exist: {file_path}",
                    line_number=line_number,
                    severity=ValidationSeverity.ERROR,
                    context=ValidationContext(
                        file_path=context.file_path,
                        line=content.split("\n")[line_number - 1],
                        validator_name=self.__class__.__name__,
                    ),
                )

        # Validate anchor if present
        if parsed.fragment and self.config.validate_anchors:
            return await self._validate_anchor(
                parsed.fragment, line_number, content, context
            )

        return None

    async def _validate_anchor(
        self,
        anchor: str,
        line_number: int,
        content: str,
        context: MDCContext,
    ) -> ValidationResult | None:
        """Validate an anchor reference.

        Args:
            anchor: The anchor to validate
            line_number: The line number where the anchor appears
            content: The full content of the file
            context: The MDC context

        Returns:
            Optional[ValidationResult]: Validation result if there's an issue, None otherwise
        """
        # Get or build anchor cache for the current file
        if context.file_path not in self._anchor_cache:
            self._anchor_cache[context.file_path] = self._build_anchor_cache(content)

        if anchor not in self._anchor_cache[context.file_path]:
            return ValidationResult(
                message=f"Invalid anchor reference: #{anchor}",
                line_number=line_number,
                severity=ValidationSeverity.ERROR,
                context=ValidationContext(
                    file_path=context.file_path,
                    line=content.split("\n")[line_number - 1],
                    validator_name=self.__class__.__name__,
                ),
            )

        return None

    def _build_anchor_cache(self, content: str) -> set[str]:
        """Build a cache of valid anchors in the content.

        Args:
            content: The content to analyze

        Returns:
            Set[str]: Set of valid anchor IDs
        """
        anchors = set()

        # Find all headers and their IDs
        header_pattern = r"^(#{1,6})\s+(.+)$"
        for match in re.finditer(header_pattern, content, re.MULTILINE):
            header_text = match.group(2)
            # Convert header text to GitHub-style anchor
            anchor_id = re.sub(r"[^\w\- ]", "", header_text.lower())
            anchor_id = re.sub(r"\s+", "-", anchor_id.strip())
            anchors.add(anchor_id)

        # Find explicit anchor tags
        anchor_pattern = r'<a\s+(?:[^>]*?\s+)?id=["\']([^"\']+)["\']'
        for match in re.finditer(anchor_pattern, content):
            anchors.add(match.group(1))

        return anchors

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

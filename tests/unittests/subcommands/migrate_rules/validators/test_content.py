"""Tests for content structure validator.

This module contains tests for the markdown content structure validator used
in the MDC validation system.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional, Set

import pytest
from pydantic import ValidationError

from contextforge_cli.subcommands.migrate_rules.models.validation import (
    ValidationContext,
    ValidationResult,
    ValidationSeverity,
)
from contextforge_cli.subcommands.migrate_rules.validators.content import (
    CodeBlockInfo,
    ContentValidator,
    ContentValidatorConfig,
    HeadingInfo,
)

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def workspace_root() -> Path:
    """Fixture providing a workspace root path.

    Returns:
        Path: An absolute path to use as workspace root
    """
    return Path("/Users/malcolm/dev/bossjones/contextforge-cli")


@pytest.fixture
def test_file(workspace_root: Path) -> Path:
    """Fixture providing a test file path.

    Args:
        workspace_root: The workspace root path

    Returns:
        Path: An absolute path to use as test file
    """
    return workspace_root / "src" / "test.mdc"


@pytest.fixture
def valid_content() -> str:
    """Fixture providing valid content structure.

    Returns:
        str: Valid content
    """
    return '''---
description: Test file
globs: ["**/*.py"]
---

# Purpose

This is a test file.

## Implementation

```python
def test():
    """Test function."""
    return True
```

### Details

More details here.
'''


@pytest.fixture
def invalid_heading_hierarchy() -> str:
    """Fixture providing content with invalid heading hierarchy.

    Returns:
        str: Content with invalid heading hierarchy
    """
    return """---
description: Test file
globs: ["**/*.py"]
---

# Purpose

### Invalid Jump
"""


@pytest.fixture
def missing_required_sections() -> str:
    """Fixture providing content with missing required sections.

    Returns:
        str: Content with missing sections
    """
    return """---
description: Test file
globs: ["**/*.py"]
---

# Introduction

Some content.
"""


@pytest.fixture
def invalid_code_blocks() -> str:
    """Fixture providing content with invalid code blocks.

    Returns:
        str: Content with invalid code blocks
    """
    return """---
description: Test file
globs: ["**/*.py"]
---

# Purpose

```
def test():
    return True
```

## Implementation

```invalid-lang
some code
```
"""


@pytest.fixture
def validation_context(
    workspace_root: Path, test_file: Path, valid_content: str
) -> ValidationContext:
    """Fixture providing a validation context.

    Args:
        workspace_root: The workspace root path
        test_file: The test file path
        valid_content: Valid content

    Returns:
        ValidationContext: A sample validation context
    """
    return ValidationContext(
        workspace_root=workspace_root,
        file_path=test_file,
        content=valid_content,
    )


class TestCodeBlockInfo:
    """Tests for CodeBlockInfo."""

    def test_valid_code_block(self) -> None:
        """Test valid code block info."""
        block = CodeBlockInfo(
            language="python",
            content="def test():\n    return True",
            start_line=1,
            end_line=3,
            indentation=4,
        )
        assert block.language == "python"
        assert "def test()" in block.content
        assert block.start_line == 1
        assert block.end_line == 3
        assert block.indentation == 4

    def test_code_block_without_language(self) -> None:
        """Test code block info without language."""
        block = CodeBlockInfo(
            content="test content",
            start_line=1,
            end_line=2,
        )
        assert block.language is None
        assert block.content == "test content"
        assert block.indentation == 0


class TestContentValidatorConfig:
    """Tests for ContentValidatorConfig."""

    def test_default_config(self) -> None:
        """Test default validator configuration."""
        config = ContentValidatorConfig()
        assert config.max_heading_level == 4
        assert "Purpose" in config.required_sections
        assert "python" in config.code_block_languages
        assert config.require_language_spec is True
        assert config.allow_raw_html is False
        assert config.max_consecutive_blank_lines == 2

    def test_custom_config(self) -> None:
        """Test custom validator configuration."""
        config = ContentValidatorConfig(
            max_heading_level=3,
            required_sections={"Custom"},
            code_block_languages={"custom-lang"},
            require_language_spec=False,
            allow_raw_html=True,
            max_consecutive_blank_lines=3,
        )
        assert config.max_heading_level == 3
        assert config.required_sections == {"Custom"}
        assert config.code_block_languages == {"custom-lang"}
        assert config.require_language_spec is False
        assert config.allow_raw_html is True
        assert config.max_consecutive_blank_lines == 3


class TestContentValidator:
    """Tests for ContentValidator."""

    @pytest.mark.asyncio
    async def test_valid_content(self, validation_context: ValidationContext) -> None:
        """Test validation of valid content structure.

        Args:
            validation_context: The validation context fixture
        """
        validator = ContentValidator()
        results = []
        async for result in validator.validate(validation_context):
            results.append(result)

        assert not any(
            r.severity == ValidationSeverity.ERROR and not r.is_valid for r in results
        )

    @pytest.mark.asyncio
    async def test_invalid_heading_hierarchy(
        self, workspace_root: Path, test_file: Path, invalid_heading_hierarchy: str
    ) -> None:
        """Test validation of invalid heading hierarchy.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
            invalid_heading_hierarchy: Content with invalid hierarchy
        """
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content=invalid_heading_hierarchy,
        )
        validator = ContentValidator()
        results = []
        async for result in validator.validate(context):
            results.append(result)

        assert any(
            "Invalid heading hierarchy" in r.message
            and not r.is_valid
            and r.severity == ValidationSeverity.ERROR
            for r in results
        )

    @pytest.mark.asyncio
    async def test_missing_required_sections(
        self, workspace_root: Path, test_file: Path, missing_required_sections: str
    ) -> None:
        """Test validation of missing required sections.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
            missing_required_sections: Content with missing sections
        """
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content=missing_required_sections,
        )
        validator = ContentValidator()
        results = []
        async for result in validator.validate(context):
            results.append(result)

        assert any(
            "Missing required sections" in r.message
            and not r.is_valid
            and r.severity == ValidationSeverity.ERROR
            for r in results
        )

    @pytest.mark.asyncio
    async def test_invalid_code_blocks(
        self, workspace_root: Path, test_file: Path, invalid_code_blocks: str
    ) -> None:
        """Test validation of invalid code blocks.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
            invalid_code_blocks: Content with invalid code blocks
        """
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content=invalid_code_blocks,
        )
        validator = ContentValidator()
        results = []
        async for result in validator.validate(context):
            results.append(result)

        assert any(
            "Code block must specify a language" in r.message
            and not r.is_valid
            and r.severity == ValidationSeverity.ERROR
            for r in results
        )

    @pytest.mark.asyncio
    async def test_raw_html_detection(
        self, workspace_root: Path, test_file: Path
    ) -> None:
        """Test detection of raw HTML.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
        """
        content = """# Title
<div>Raw HTML</div>
"""
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content=content,
        )
        validator = ContentValidator()
        results = []
        async for result in validator.validate(context):
            results.append(result)

        assert any(
            "Raw HTML is not allowed" in r.message
            and not r.is_valid
            and r.severity == ValidationSeverity.ERROR
            for r in results
        )

    @pytest.mark.asyncio
    async def test_consecutive_blank_lines(
        self, workspace_root: Path, test_file: Path
    ) -> None:
        """Test detection of too many consecutive blank lines.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
        """
        content = """# Title

First paragraph.



Second paragraph.
"""
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content=content,
        )
        validator = ContentValidator()
        results = []
        async for result in validator.validate(context):
            results.append(result)

        assert any(
            "Too many consecutive blank lines" in r.message
            and not r.is_valid
            and r.severity == ValidationSeverity.WARNING
            for r in results
        )

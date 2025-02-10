"""Tests for frontmatter validator.

This module contains tests for the YAML frontmatter validator used in the MDC
validation system.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Optional

import pytest
import yaml
from pydantic import ValidationError

from contextforge_cli.subcommands.migrate_rules.models.validation import (
    ValidationContext,
    ValidationResult,
    ValidationSeverity,
)
from contextforge_cli.subcommands.migrate_rules.validators.frontmatter import (
    FrontmatterSchema,
    FrontmatterValidator,
    FrontmatterValidatorConfig,
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
def valid_frontmatter() -> str:
    """Fixture providing valid frontmatter content.

    Returns:
        str: Valid frontmatter content
    """
    return """---
description: A test MDC file
globs: ["**/*.py", "tests/**/*.py"]
related_docs: ["docs/test.md"]
---
# Content
"""


@pytest.fixture
def invalid_frontmatter() -> str:
    """Fixture providing invalid frontmatter content.

    Returns:
        str: Invalid frontmatter content
    """
    return """---
description: [Invalid description type]
globs: "Invalid globs type"
related_docs: "Invalid related_docs type"
---
# Content
"""


@pytest.fixture
def missing_required_frontmatter() -> str:
    """Fixture providing frontmatter with missing required fields.

    Returns:
        str: Frontmatter content with missing fields
    """
    return """---
description: A test MDC file
---
# Content
"""


@pytest.fixture
def validation_context(
    workspace_root: Path, test_file: Path, valid_frontmatter: str
) -> ValidationContext:
    """Fixture providing a validation context.

    Args:
        workspace_root: The workspace root path
        test_file: The test file path
        valid_frontmatter: Valid frontmatter content

    Returns:
        ValidationContext: A sample validation context
    """
    return ValidationContext(
        workspace_root=workspace_root,
        file_path=test_file,
        content=valid_frontmatter,
    )


class TestFrontmatterSchema:
    """Tests for FrontmatterSchema."""

    def test_valid_schema(self) -> None:
        """Test valid frontmatter schema."""
        data = {
            "description": "Test description",
            "globs": ["**/*.py"],
            "related_docs": ["docs/test.md"],
        }
        schema = FrontmatterSchema(**data)
        assert schema.description == "Test description"
        assert schema.globs == ["**/*.py"]
        assert schema.related_docs == ["docs/test.md"]

    def test_missing_optional_field(self) -> None:
        """Test frontmatter schema with missing optional field."""
        data = {
            "description": "Test description",
            "globs": ["**/*.py"],
        }
        schema = FrontmatterSchema(**data)
        assert schema.description == "Test description"
        assert schema.globs == ["**/*.py"]
        assert schema.related_docs is None

    def test_invalid_schema(self) -> None:
        """Test invalid frontmatter schema."""
        data = {
            "description": ["Invalid description type"],
            "globs": "Invalid globs type",
        }
        with pytest.raises(ValidationError):
            FrontmatterSchema(**data)


class TestFrontmatterValidatorConfig:
    """Tests for FrontmatterValidatorConfig."""

    def test_default_config(self) -> None:
        """Test default validator configuration."""
        config = FrontmatterValidatorConfig()
        assert config.required_fields == {"description", "globs"}
        assert config.allow_extra_fields is False
        assert config.max_description_length == 100
        assert config.custom_schema is None

    def test_custom_config(self) -> None:
        """Test custom validator configuration."""
        config = FrontmatterValidatorConfig(
            required_fields={"test_field"},
            allow_extra_fields=True,
            max_description_length=50,
            custom_schema={"test": "schema"},
        )
        assert config.required_fields == {"test_field"}
        assert config.allow_extra_fields is True
        assert config.max_description_length == 50
        assert config.custom_schema == {"test": "schema"}


class TestFrontmatterValidator:
    """Tests for FrontmatterValidator."""

    @pytest.mark.asyncio
    async def test_valid_frontmatter(
        self, validation_context: ValidationContext
    ) -> None:
        """Test validation of valid frontmatter.

        Args:
            validation_context: The validation context fixture
        """
        validator = FrontmatterValidator()
        results = []
        async for result in validator.validate(validation_context):
            results.append(result)

        assert len(results) == 1
        assert results[0].is_valid is True
        assert results[0].severity == ValidationSeverity.INFO

    @pytest.mark.asyncio
    async def test_missing_frontmatter(
        self, workspace_root: Path, test_file: Path
    ) -> None:
        """Test validation of missing frontmatter.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
        """
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content="# No frontmatter\nContent",
        )
        validator = FrontmatterValidator()
        results = []
        async for result in validator.validate(context):
            results.append(result)

        assert len(results) == 1
        assert results[0].is_valid is False
        assert results[0].severity == ValidationSeverity.ERROR
        assert "must be at the start" in results[0].message

    @pytest.mark.asyncio
    async def test_invalid_yaml(self, workspace_root: Path, test_file: Path) -> None:
        """Test validation of invalid YAML syntax.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
        """
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content="---\nInvalid: [YAML: syntax}\n---\n",
        )
        validator = FrontmatterValidator()
        results = []
        async for result in validator.validate(context):
            results.append(result)

        assert len(results) == 1
        assert results[0].is_valid is False
        assert results[0].severity == ValidationSeverity.ERROR
        assert "Invalid YAML syntax" in results[0].message

    @pytest.mark.asyncio
    async def test_missing_required_fields(
        self, workspace_root: Path, test_file: Path, missing_required_frontmatter: str
    ) -> None:
        """Test validation of frontmatter with missing required fields.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
            missing_required_frontmatter: Frontmatter content with missing fields
        """
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content=missing_required_frontmatter,
        )
        validator = FrontmatterValidator()
        results = []
        async for result in validator.validate(context):
            results.append(result)

        assert len(results) == 1
        assert results[0].is_valid is False
        assert results[0].severity == ValidationSeverity.ERROR
        assert "Schema validation failed" in results[0].message

    @pytest.mark.asyncio
    async def test_long_description(
        self, workspace_root: Path, test_file: Path
    ) -> None:
        """Test validation of frontmatter with too-long description.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
        """
        long_description = "x" * 101
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content=f"---\ndescription: {long_description}\nglobs: ['**/*.py']\n---\n",
        )
        validator = FrontmatterValidator()
        results = []
        async for result in validator.validate(context):
            results.append(result)

        assert len(results) == 1
        assert results[0].is_valid is False
        assert results[0].severity == ValidationSeverity.ERROR
        assert "exceeds maximum length" in results[0].message

    @pytest.mark.asyncio
    async def test_missing_related_doc(
        self, workspace_root: Path, test_file: Path
    ) -> None:
        """Test validation of frontmatter with missing related document.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
        """
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content="---\ndescription: Test\nglobs: ['**/*.py']\nrelated_docs: ['nonexistent.md']\n---\n",
        )
        validator = FrontmatterValidator()
        results = []
        async for result in validator.validate(context):
            results.append(result)

        assert len(results) == 1
        assert results[0].is_valid is False
        assert results[0].severity == ValidationSeverity.ERROR
        assert "does not exist" in results[0].message

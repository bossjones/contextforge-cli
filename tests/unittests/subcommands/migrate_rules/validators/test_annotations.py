"""Tests for annotation validator.

This module contains tests for the @annotation validator used in the MDC
validation system.
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
from contextforge_cli.subcommands.migrate_rules.validators.annotations import (
    AnnotationSchema,
    AnnotationValidator,
    AnnotationValidatorConfig,
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
def valid_annotations() -> str:
    """Fixture providing valid annotation content.

    Returns:
        str: Valid annotation content
    """
    return """---
description: Test file
globs: ["**/*.py"]
---

@context {
    "type": "implementation",
    "feature": "test",
    "version": "1.0.0"
}

@implementation {
    "language": "python",
    "dependencies": ["pytest>=7.0.0"]
}
"""


@pytest.fixture
def invalid_json_annotation() -> str:
    """Fixture providing annotation with invalid JSON.

    Returns:
        str: Content with invalid JSON annotation
    """
    return """---
description: Test file
globs: ["**/*.py"]
---

@context {
    "type": "implementation"
    "invalid": "json",
}
"""


@pytest.fixture
def unknown_annotation_type() -> str:
    """Fixture providing content with unknown annotation type.

    Returns:
        str: Content with unknown annotation type
    """
    return """---
description: Test file
globs: ["**/*.py"]
---

@unknown {
    "test": "value"
}
"""


@pytest.fixture
def missing_required_annotations() -> str:
    """Fixture providing content missing required annotations.

    Returns:
        str: Content missing required annotations
    """
    return """---
description: Test file
globs: ["**/*.py"]
---

@rules {
    "test": "value"
}
"""


@pytest.fixture
def validation_context(
    workspace_root: Path, test_file: Path, valid_annotations: str
) -> ValidationContext:
    """Fixture providing a validation context.

    Args:
        workspace_root: The workspace root path
        test_file: The test file path
        valid_annotations: Valid annotation content

    Returns:
        ValidationContext: A sample validation context
    """
    return ValidationContext(
        workspace_root=workspace_root,
        file_path=test_file,
        content=valid_annotations,
    )


class TestAnnotationSchema:
    """Tests for AnnotationSchema."""

    def test_valid_schema(self) -> None:
        """Test valid annotation schema."""
        data = {
            "type": "context",
            "content": {"test": "value"},
        }
        schema = AnnotationSchema(**data)
        assert schema.type == "context"
        assert schema.content == {"test": "value"}

    def test_invalid_schema(self) -> None:
        """Test invalid annotation schema."""
        data = {
            "type": ["invalid type"],
            "content": "invalid content",
        }
        with pytest.raises(ValidationError):
            AnnotationSchema(**data)


class TestAnnotationValidatorConfig:
    """Tests for AnnotationValidatorConfig."""

    def test_default_config(self) -> None:
        """Test default validator configuration."""
        config = AnnotationValidatorConfig()
        assert "context" in config.required_annotations
        assert "implementation" in config.required_annotations
        assert config.allow_unknown_types is False
        assert "context" in config.known_types
        assert isinstance(config.annotation_pattern, str)

    def test_custom_config(self) -> None:
        """Test custom validator configuration."""
        config = AnnotationValidatorConfig(
            required_annotations={"test"},
            allow_unknown_types=True,
            known_types={"test"},
            annotation_pattern=r"@test\s*({.*})",
        )
        assert config.required_annotations == {"test"}
        assert config.allow_unknown_types is True
        assert config.known_types == {"test"}
        assert config.annotation_pattern == r"@test\s*({.*})"


class TestAnnotationValidator:
    """Tests for AnnotationValidator."""

    @pytest.mark.asyncio
    async def test_valid_annotations(
        self, validation_context: ValidationContext
    ) -> None:
        """Test validation of valid annotations.

        Args:
            validation_context: The validation context fixture
        """
        validator = AnnotationValidator()
        results = []
        async for result in validator.validate(validation_context):
            results.append(result)

        assert all(r.is_valid for r in results)
        assert len(results) == 2  # @context and @implementation

    @pytest.mark.asyncio
    async def test_invalid_json(
        self, workspace_root: Path, test_file: Path, invalid_json_annotation: str
    ) -> None:
        """Test validation of invalid JSON syntax.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
            invalid_json_annotation: Content with invalid JSON
        """
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content=invalid_json_annotation,
        )
        validator = AnnotationValidator()
        results = []
        async for result in validator.validate(context):
            results.append(result)

        assert any(not r.is_valid for r in results)
        assert any("Invalid JSON syntax" in r.message for r in results)

    @pytest.mark.asyncio
    async def test_unknown_annotation_type(
        self, workspace_root: Path, test_file: Path, unknown_annotation_type: str
    ) -> None:
        """Test validation of unknown annotation type.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
            unknown_annotation_type: Content with unknown annotation type
        """
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content=unknown_annotation_type,
        )
        validator = AnnotationValidator()
        results = []
        async for result in validator.validate(context):
            results.append(result)

        assert any(not r.is_valid for r in results)
        assert any("Unknown annotation type" in r.message for r in results)

    @pytest.mark.asyncio
    async def test_missing_required_annotations(
        self, workspace_root: Path, test_file: Path, missing_required_annotations: str
    ) -> None:
        """Test validation of missing required annotations.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
            missing_required_annotations: Content missing required annotations
        """
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content=missing_required_annotations,
        )
        validator = AnnotationValidator()
        results = []
        async for result in validator.validate(context):
            results.append(result)

        assert any(not r.is_valid for r in results)
        assert any("Missing required annotations" in r.message for r in results)

    @pytest.mark.asyncio
    async def test_allow_unknown_types(
        self, workspace_root: Path, test_file: Path, unknown_annotation_type: str
    ) -> None:
        """Test validation with unknown types allowed.

        Args:
            workspace_root: The workspace root path
            test_file: The test file path
            unknown_annotation_type: Content with unknown annotation type
        """
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content=unknown_annotation_type,
        )
        config = AnnotationValidatorConfig(allow_unknown_types=True)
        validator = AnnotationValidator(config=config)
        results = []
        async for result in validator.validate(context):
            results.append(result)

        # Should still fail due to missing required annotations
        assert any(not r.is_valid for r in results)
        assert not any("Unknown annotation type" in r.message for r in results)

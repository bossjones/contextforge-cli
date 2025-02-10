"""Tests for validation models.

This module contains tests for the validation result models used in the MDC
validation system.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Dict

import pytest
from pydantic import ValidationError

from contextforge_cli.subcommands.migrate_rules.models.validation import (
    ValidationContext,
    ValidationLocation,
    ValidationResult,
    ValidationSeverity,
    ValidationSummary,
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
def validation_location() -> ValidationLocation:
    """Fixture providing a validation location.

    Returns:
        ValidationLocation: A sample validation location
    """
    return ValidationLocation(
        line=10,
        column=5,
        section="frontmatter",
        context="description: test",
    )


@pytest.fixture
def validation_result(validation_location: ValidationLocation) -> ValidationResult:
    """Fixture providing a validation result.

    Args:
        validation_location: The validation location to use

    Returns:
        ValidationResult: A sample validation result
    """
    return ValidationResult(
        is_valid=False,
        severity=ValidationSeverity.ERROR,
        message="Test validation error",
        location=validation_location,
        details={"test_key": "test_value"},
        rule_id="TEST001",
    )


@pytest.fixture
def validation_context(workspace_root: Path, test_file: Path) -> ValidationContext:
    """Fixture providing a validation context.

    Args:
        workspace_root: The workspace root path
        test_file: The test file path

    Returns:
        ValidationContext: A sample validation context
    """
    return ValidationContext(
        workspace_root=workspace_root,
        file_path=test_file,
        content="Test content",
        related_files={test_file: "Related content"},
        config={"test_key": "test_value"},
    )


class TestValidationLocation:
    """Tests for ValidationLocation model."""

    def test_create_validation_location(self) -> None:
        """Test creating a ValidationLocation."""
        location = ValidationLocation(
            line=1,
            column=1,
            section="test",
            context="test context",
        )
        assert location.line == 1
        assert location.column == 1
        assert location.section == "test"
        assert location.context == "test context"

    def test_validation_location_str(
        self, validation_location: ValidationLocation
    ) -> None:
        """Test string representation of ValidationLocation.

        Args:
            validation_location: The validation location fixture
        """
        str_repr = str(validation_location)
        assert "section: frontmatter" in str_repr
        assert "line: 10" in str_repr
        assert "column: 5" in str_repr


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_create_validation_result(
        self, validation_location: ValidationLocation
    ) -> None:
        """Test creating a ValidationResult.

        Args:
            validation_location: The validation location fixture
        """
        result = ValidationResult(
            is_valid=True,
            message="Test message",
            location=validation_location,
        )
        assert result.is_valid is True
        assert result.message == "Test message"
        assert result.location == validation_location
        assert result.severity == ValidationSeverity.ERROR  # default severity

    def test_validation_result_str(self, validation_result: ValidationResult) -> None:
        """Test string representation of ValidationResult.

        Args:
            validation_result: The validation result fixture
        """
        str_repr = str(validation_result)
        assert "[ERROR]" in str_repr
        assert "FAIL" in str_repr
        assert "Test validation error" in str_repr
        assert "test_key: test_value" in str_repr


class TestValidationContext:
    """Tests for ValidationContext model."""

    def test_create_validation_context(
        self, workspace_root: Path, test_file: Path
    ) -> None:
        """Test creating a ValidationContext.

        Args:
            workspace_root: The workspace root path fixture
            test_file: The test file path fixture
        """
        context = ValidationContext(
            workspace_root=workspace_root,
            file_path=test_file,
            content="Test content",
        )
        assert context.workspace_root == workspace_root
        assert context.file_path == test_file
        assert context.content == "Test content"

    def test_validation_context_path_validation(
        self, workspace_root: Path, test_file: Path
    ) -> None:
        """Test path validation in ValidationContext.

        Args:
            workspace_root: The workspace root path fixture
            test_file: The test file path fixture
        """
        # Test relative path rejection
        with pytest.raises(ValueError, match="Path must be absolute"):
            ValidationContext(
                workspace_root="relative/path",
                file_path=test_file,
                content="Test content",
            )

        # Test file path outside workspace
        with pytest.raises(ValueError, match="File path must be within workspace root"):
            ValidationContext(
                workspace_root=workspace_root,
                file_path=Path("/other/path/file.mdc"),
                content="Test content",
            )


class TestValidationSummary:
    """Tests for ValidationSummary model."""

    def test_create_validation_summary(
        self, test_file: Path, validation_result: ValidationResult
    ) -> None:
        """Test creating a ValidationSummary.

        Args:
            test_file: The test file path fixture
            validation_result: The validation result fixture
        """
        summary = ValidationSummary(
            file_path=test_file,
            is_valid=False,
            results=[validation_result],
            error_count=1,
            warning_count=0,
            info_count=0,
        )
        assert summary.file_path == test_file
        assert summary.is_valid is False
        assert len(summary.results) == 1
        assert summary.error_count == 1

    def test_validation_summary_str(
        self, test_file: Path, validation_result: ValidationResult
    ) -> None:
        """Test string representation of ValidationSummary.

        Args:
            test_file: The test file path fixture
            validation_result: The validation result fixture
        """
        summary = ValidationSummary(
            file_path=test_file,
            is_valid=False,
            results=[validation_result],
            error_count=1,
            warning_count=0,
            info_count=0,
        )
        str_repr = str(summary)
        assert str(test_file) in str_repr
        assert "FAIL" in str_repr
        assert "Errors: 1" in str_repr

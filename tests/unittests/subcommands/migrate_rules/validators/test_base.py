"""Tests for base validator classes.

This module contains tests for the base validator classes and validation pipeline
used in the MDC validation system.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

import pytest
import structlog

from contextforge_cli.subcommands.migrate_rules.models.validation import (
    ValidationContext,
    ValidationResult,
    ValidationSeverity,
    ValidationSummary,
)
from contextforge_cli.subcommands.migrate_rules.validators.base import (
    BaseValidator,
    ValidationPipeline,
    ValidatorConfig,
)

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from pytest_mock.plugin import MockerFixture


class TestValidator(BaseValidator):
    """Test implementation of BaseValidator."""

    def __init__(
        self,
        name: str = "test",
        description: str = "Test validator",
        config: ValidatorConfig | None = None,
        results: list[ValidationResult] | None = None,
        should_raise: bool = False,
    ) -> None:
        """Initialize TestValidator.

        Args:
            name: Name of the validator
            description: Description of what this validator checks
            config: Optional validator configuration
            results: Optional list of results to return
            should_raise: Whether the validator should raise an exception
        """
        super().__init__(name, description, config)
        self.results = results or []
        self.should_raise = should_raise
        self.cleanup_called = False

    async def validate(
        self, context: ValidationContext
    ) -> AsyncGenerator[ValidationResult, None]:
        """Test validation implementation.

        Args:
            context: Validation context

        Yields:
            ValidationResult objects

        Raises:
            Exception: If should_raise is True
        """
        if self.should_raise:
            raise Exception("Test validation error")
        for result in self.results:
            yield result

    async def cleanup(self) -> None:
        """Test cleanup implementation."""
        self.cleanup_called = True


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
    )


@pytest.fixture
def test_results() -> list[ValidationResult]:
    """Fixture providing test validation results.

    Returns:
        List[ValidationResult]: A list of sample validation results
    """
    return [
        ValidationResult(
            is_valid=True,
            message="Test success",
            severity=ValidationSeverity.INFO,
        ),
        ValidationResult(
            is_valid=False,
            message="Test error",
            severity=ValidationSeverity.ERROR,
        ),
    ]


class TestValidatorConfig:
    """Tests for ValidatorConfig."""

    def test_create_validator_config(self) -> None:
        """Test creating a ValidatorConfig."""
        config = ValidatorConfig(
            enabled=True,
            severity_overrides={"TEST001": ValidationSeverity.WARNING},
            custom_rules={"test_rule": "test_value"},
            max_concurrent=5,
        )
        assert config.enabled is True
        assert config.severity_overrides == {"TEST001": ValidationSeverity.WARNING}
        assert config.custom_rules == {"test_rule": "test_value"}
        assert config.max_concurrent == 5

    def test_validator_config_defaults(self) -> None:
        """Test ValidatorConfig default values."""
        config = ValidatorConfig()
        assert config.enabled is True
        assert config.severity_overrides == {}
        assert config.custom_rules == {}
        assert config.max_concurrent == 10


class TestBaseValidator:
    """Tests for BaseValidator."""

    @pytest.mark.asyncio
    async def test_validator_validation(
        self,
        validation_context: ValidationContext,
        test_results: list[ValidationResult],
    ) -> None:
        """Test validator validation.

        Args:
            validation_context: The validation context fixture
            test_results: The test results fixture
        """
        validator = TestValidator(results=test_results)
        results = []
        async for result in validator.validate(validation_context):
            results.append(result)
        assert results == test_results

    @pytest.mark.asyncio
    async def test_validator_cleanup(self) -> None:
        """Test validator cleanup."""
        validator = TestValidator()
        await validator.cleanup()
        assert validator.cleanup_called is True

    def test_get_severity(self) -> None:
        """Test getting rule severity with overrides."""
        config = ValidatorConfig(
            severity_overrides={"TEST001": ValidationSeverity.WARNING}
        )
        validator = TestValidator(config=config)
        assert validator.get_severity("TEST001") == ValidationSeverity.WARNING
        assert validator.get_severity("TEST002") == ValidationSeverity.ERROR


class TestValidationPipeline:
    """Tests for ValidationPipeline."""

    @pytest.mark.asyncio
    async def test_validation_pipeline_sequential(
        self,
        validation_context: ValidationContext,
        test_results: list[ValidationResult],
    ) -> None:
        """Test sequential validation pipeline.

        Args:
            validation_context: The validation context fixture
            test_results: The test results fixture
        """
        validators = [
            TestValidator(name="test1", results=test_results),
            TestValidator(name="test2", results=test_results),
        ]
        pipeline = ValidationPipeline(validators, parallel=False)
        summary = await pipeline.validate(validation_context)

        assert len(summary.results) == 4  # 2 validators * 2 results each
        assert summary.error_count == 2  # 2 validators * 1 error each
        assert summary.is_valid is False

    @pytest.mark.asyncio
    async def test_validation_pipeline_parallel(
        self,
        validation_context: ValidationContext,
        test_results: list[ValidationResult],
    ) -> None:
        """Test parallel validation pipeline.

        Args:
            validation_context: The validation context fixture
            test_results: The test results fixture
        """
        validators = [
            TestValidator(name="test1", results=test_results),
            TestValidator(name="test2", results=test_results),
        ]
        pipeline = ValidationPipeline(validators, parallel=True, max_concurrent=2)
        summary = await pipeline.validate(validation_context)

        assert len(summary.results) == 4  # 2 validators * 2 results each
        assert summary.error_count == 2  # 2 validators * 1 error each
        assert summary.is_valid is False

    @pytest.mark.asyncio
    async def test_validation_pipeline_error_handling(
        self, validation_context: ValidationContext
    ) -> None:
        """Test validation pipeline error handling.

        Args:
            validation_context: The validation context fixture
        """
        validators = [
            TestValidator(name="test1", should_raise=True),
            TestValidator(name="test2", results=[]),
        ]
        pipeline = ValidationPipeline(validators)
        summary = await pipeline.validate(validation_context)

        assert len(summary.results) == 1  # Error result from failed validator
        assert summary.error_count == 1
        assert summary.is_valid is False
        assert "Test validation error" in summary.results[0].message

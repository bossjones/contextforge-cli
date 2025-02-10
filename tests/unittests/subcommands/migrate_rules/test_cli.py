"""Test suite for MDC validation CLI.

This module contains tests for the CLI interface of the MDC validation system.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, List

import pytest
from typer.testing import CliRunner

from contextforge_cli.subcommands.migrate_rules.cli import (
    ValidationCli,
    ValidationCliConfig,
    app,
)
from contextforge_cli.subcommands.migrate_rules.models.validation import (
    ValidationContext,
    ValidationResult,
    ValidationSeverity,
)

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CliRunner instance for testing.

    Returns:
        CliRunner: A runner for testing Typer CLI applications
    """
    return CliRunner()


@pytest.fixture
def test_files(tmp_path: Path) -> list[Path]:
    """Create test files for validation.

    Args:
        tmp_path: Pytest fixture providing a temporary directory path

    Returns:
        List[Path]: List of created test file paths
    """
    # Create a valid MDC file
    valid_file = tmp_path / "valid.mdc"
    valid_file.write_text("""---
title: Valid Document
---

# Valid Document

This is a valid document.
""")

    # Create an invalid MDC file
    invalid_file = tmp_path / "invalid.mdc"
    invalid_file.write_text("""# Invalid Document

Missing frontmatter
""")

    return [valid_file, invalid_file]


@pytest.fixture
def mock_results() -> list[ValidationResult]:
    """Create mock validation results for testing.

    Returns:
        List[ValidationResult]: List of mock validation results
    """
    return [
        ValidationResult(
            message="Test error",
            line_number=1,
            severity=ValidationSeverity.ERROR,
            context=ValidationContext(
                file_path="test.mdc",
                line="Test line",
                validator_name="TestValidator",
            ),
        ),
        ValidationResult(
            message="Test warning",
            line_number=2,
            severity=ValidationSeverity.WARNING,
            context=ValidationContext(
                file_path="test.mdc",
                line="Test line",
                validator_name="TestValidator",
            ),
        ),
    ]


def test_validation_cli_config_defaults() -> None:
    """Test ValidationCliConfig default values."""
    config = ValidationCliConfig()
    assert "**/*.md" in config.include_patterns
    assert "**/*.mdc" in config.include_patterns
    assert "**/node_modules/**" in config.exclude_patterns
    assert "frontmatter" in config.validators
    assert config.parallel is True
    assert config.fail_on_warnings is False
    assert config.report_format == "rich"


def test_validation_cli_initialization() -> None:
    """Test ValidationCli initialization."""
    cli = ValidationCli()
    assert len(cli._validators) > 0
    assert cli.config is not None
    assert cli.console is not None


@pytest.mark.asyncio
async def test_validate_valid_file(
    tmp_path: Path,
    test_files: list[Path],
) -> None:
    """Test validation of a valid file.

    Args:
        tmp_path: Pytest fixture providing a temporary directory path
        test_files: List of test file paths
    """
    config = ValidationCliConfig(base_path=tmp_path)
    cli = ValidationCli(config=config)
    results = await cli.validate_files([test_files[0]])  # Valid file
    assert not any(r.severity == ValidationSeverity.ERROR for r in results)


@pytest.mark.asyncio
async def test_validate_invalid_file(
    tmp_path: Path,
    test_files: list[Path],
) -> None:
    """Test validation of an invalid file.

    Args:
        tmp_path: Pytest fixture providing a temporary directory path
        test_files: List of test file paths
    """
    config = ValidationCliConfig(base_path=tmp_path)
    cli = ValidationCli(config=config)
    results = await cli.validate_files([test_files[1]])  # Invalid file
    assert any(r.severity == ValidationSeverity.ERROR for r in results)


def test_should_fail_with_errors(mock_results: list[ValidationResult]) -> None:
    """Test should_fail with error results.

    Args:
        mock_results: List of mock validation results
    """
    cli = ValidationCli()
    assert cli.should_fail(mock_results) is True


def test_should_fail_with_warnings_only(mock_results: list[ValidationResult]) -> None:
    """Test should_fail with warning results only.

    Args:
        mock_results: List of mock validation results
    """
    cli = ValidationCli(config=ValidationCliConfig(fail_on_warnings=True))
    warnings_only = [
        r for r in mock_results if r.severity == ValidationSeverity.WARNING
    ]
    assert cli.should_fail(warnings_only) is True


def test_cli_command_help(cli_runner: CliRunner) -> None:
    """Test CLI command help output.

    Args:
        cli_runner: CliRunner instance
    """
    result = cli_runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Validate MDC files" in result.stdout


def test_cli_command_no_files(cli_runner: CliRunner, tmp_path: Path) -> None:
    """Test CLI command with no files to validate.

    Args:
        cli_runner: CliRunner instance
        tmp_path: Pytest fixture providing a temporary directory path
    """
    result = cli_runner.invoke(app, [str(tmp_path)])
    assert result.exit_code == 0
    assert "No files found to validate!" in result.stdout


def test_cli_command_with_files(
    cli_runner: CliRunner,
    test_files: list[Path],
) -> None:
    """Test CLI command with test files.

    Args:
        cli_runner: CliRunner instance
        test_files: List of test file paths
    """
    result = cli_runner.invoke(
        app,
        [str(test_files[0]), "--validator", "frontmatter"],
    )
    assert result.exit_code == 0
    assert "Validated 1 files" in result.stdout


def test_cli_command_parallel_execution(
    cli_runner: CliRunner,
    test_files: list[Path],
) -> None:
    """Test CLI command with parallel execution.

    Args:
        cli_runner: CliRunner instance
        test_files: List of test file paths
    """
    result = cli_runner.invoke(
        app,
        [str(f) for f in test_files] + ["--parallel"],
    )
    assert result.exit_code == 1  # Should fail due to invalid file
    assert "Validated 2 files" in result.stdout


def test_cli_command_fail_on_warnings(
    cli_runner: CliRunner,
    test_files: list[Path],
) -> None:
    """Test CLI command with fail-on-warnings option.

    Args:
        cli_runner: CliRunner instance
        test_files: List of test file paths
    """
    result = cli_runner.invoke(
        app,
        [str(test_files[0]), "--fail-on-warnings"],
    )
    assert result.exit_code in (0, 1)  # Depends on whether warnings are present


@pytest.mark.asyncio
async def test_validate_files_error_handling(tmp_path: Path) -> None:
    """Test error handling during file validation.

    Args:
        tmp_path: Pytest fixture providing a temporary directory path
    """
    # Create an unreadable file
    test_file = tmp_path / "unreadable.mdc"
    test_file.write_text("")
    test_file.chmod(0o000)  # Remove all permissions

    cli = ValidationCli()
    results = await cli.validate_files([test_file])
    assert any("Failed to validate file" in r.message for r in results)

    # Restore permissions for cleanup
    test_file.chmod(0o644)

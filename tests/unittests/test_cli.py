from __future__ import annotations

import logging
import sys
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
import structlog
from typer.testing import CliRunner

import contextforge_cli
from contextforge_cli.cli import APP
from contextforge_cli.subcommands.async_cmd import async_operation

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create a CLI runner for testing.

    Returns:
        CliRunner: Configured CLI test runner
    """
    return CliRunner()


@pytest.fixture(autouse=True)
def setup_logging() -> Generator[None, None, None]:
    """Configure structlog for testing.

    Yields:
        None
    """
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.testing.capture_logs,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG),
        context_class=dict,
        logger_factory=structlog.testing.LogCapture,
        cache_logger_on_first_use=True,
    )
    yield


def test_version_command(cli_runner: CliRunner) -> None:
    """Test the version command output.

    Args:
        cli_runner: The CLI test runner
    """
    result = cli_runner.invoke(APP, ["version"])
    assert result.exit_code == 0
    assert f"contextforge_cli version: {contextforge_cli.__version__}" in result.stdout


def test_version_command_verbose(cli_runner: CliRunner) -> None:
    """Test the version command with verbose flag.

    Args:
        cli_runner: The CLI test runner
    """
    result = cli_runner.invoke(APP, ["version", "--verbose"])
    assert result.exit_code == 0
    assert f"contextforge_cli version: {contextforge_cli.__version__}" in result.stdout
    assert "Python version:" in result.stdout


def test_deps_command(cli_runner: CliRunner) -> None:
    """Test the deps command output.

    Args:
        cli_runner: The CLI test runner
    """
    result = cli_runner.invoke(APP, ["deps"])
    assert result.exit_code == 0
    assert f"contextforge_cli version: {contextforge_cli.__version__}" in result.stdout
    assert "langchain_version:" in result.stdout
    assert "pydantic_version:" in result.stdout


def test_about_command(cli_runner: CliRunner) -> None:
    """Test the about command output.

    Args:
        cli_runner: The CLI test runner
    """
    result = cli_runner.invoke(APP, ["about"])
    assert result.exit_code == 0
    assert "This is GoobBot CLI" in result.stdout


def test_show_command(cli_runner: CliRunner) -> None:
    """Test the show command output.

    Args:
        cli_runner: The CLI test runner
    """
    result = cli_runner.invoke(APP, ["show"])
    assert result.exit_code == 0
    assert "Show contextforge_cli" in result.stdout


@pytest.mark.skip(reason="load_commands functionality needs to be mocked")
def test_run_load_commands(cli_runner: CliRunner) -> None:
    """Test the run_load_commands command.

    Args:
        cli_runner: The CLI test runner
    """
    result = cli_runner.invoke(APP, ["run-load-commands"])
    assert result.exit_code == 0
    assert "Loading subcommands" in result.stdout


def test_go_command(cli_runner: CliRunner) -> None:
    """Test the go command output.

    Args:
        cli_runner: The CLI test runner
    """
    result = cli_runner.invoke(APP, ["go"])
    assert result.exit_code == 0
    assert "Starting up DemocracyBot" in result.stdout


@pytest.mark.skip(reason="skipping for now")
@pytest.mark.asyncio
async def test_async_command(cli_runner: CliRunner, mocker: MockerFixture) -> None:
    """Test an async command execution.

    Args:
        cli_runner: The CLI test runner
        mocker: Pytest mocker fixture
    """
    mock_async_operation = mocker.patch(
        "contextforge_cli.subcommands.async_operation", return_value="success"
    )

    result = await cli_runner.invoke_async(APP, ["async-command"])
    assert result.exit_code == 0
    assert mock_async_operation.called


@pytest.mark.skip(reason="process command not implemented yet")
def test_command_with_options(
    cli_runner: CliRunner,
    tmp_path: Path,
) -> None:
    """Test command with various options and logging.

    Args:
        cli_runner: The CLI test runner
        tmp_path: Temporary path fixture
    """
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    with structlog.testing.capture_logs() as captured:
        result = cli_runner.invoke(
            APP, ["process", "--input-file", str(test_file), "--verbose"]
        )

        assert result.exit_code == 0
        assert any("Processing file" in log.get("event", "") for log in captured), (
            "Expected 'Processing file' log message not found"
        )

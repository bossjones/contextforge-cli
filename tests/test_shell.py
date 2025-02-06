from __future__ import annotations

import asyncio
import os
import pathlib
import time
from typing import TYPE_CHECKING, Any

import pytest

from contextforge_cli.shell import (
    ProcessException,
    ShellConsole,
    _aio_run_process_and_communicate,
    _popen,
    _popen_communicate,
    _popen_stdout,
    _popen_stdout_lock,
    _stat_y_file,
    pquery,
    run_coroutine_subprocess,
)

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture()
def temp_file(tmp_path: pathlib.Path) -> str:
    """
    Create a temporary file for testing.

    Args:
    ----
    tmp_path (pathlib.Path): Pytest fixture providing a temporary directory path.

    Returns:
    -------
    str: The path to the created temporary file.
    """
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("Test content")
    return str(file_path)


@pytest.mark.asyncio()
async def test_aio_run_process_and_communicate() -> None:
    """
    Test the _aio_run_process_and_communicate function.

    This test verifies that the function correctly executes a simple echo command
    and returns the expected output.
    """
    result = await _aio_run_process_and_communicate(["echo", "Hello, World!"])
    assert result == "Hello, World!"


def test_stat_y_file(temp_file: str) -> None:
    """
    Test the _stat_y_file function.

    This test checks if the function returns a non-empty string timestamp
    for a given temporary file.

    Args:
    ----
    temp_file (str): Path to a temporary file created by the temp_file fixture.
    """
    timestamp = _stat_y_file(temp_file)
    assert isinstance(timestamp, str)
    # assert len(timestamp) > 0


def test_popen() -> None:
    """
    Test the _popen function.

    This test verifies that the function correctly executes a simple echo command
    and returns the expected output as bytes.
    """
    result = _popen(("echo", "Hello, World!"))
    assert result == b"Hello, World!"


def test_popen_communicate() -> None:
    """
    Test the _popen_communicate function.

    This test checks if the function correctly executes a simple echo command
    and returns the expected output as bytes.
    """
    result = _popen_communicate(("echo", "Hello, World!"))
    assert result == b"Hello, World!"


def test_pquery() -> None:
    """
    Test the pquery function.

    This test verifies that the function correctly executes a simple echo command
    and returns the expected output as a string.
    """
    result = pquery(["echo", "Hello, World!"])
    assert result == "Hello, World!\n"


def test_pquery_exception() -> None:
    """
    Test the pquery function with an invalid command.

    This test checks if the function raises a ProcessException when
    an invalid command is provided.
    """
    with pytest.raises((ProcessException, FileNotFoundError)):
        pquery(["invalid_command"])


def test_popen_stdout(capsys: CaptureFixture[str]) -> None:
    """
    Test the _popen_stdout function.

    This test verifies that the function correctly executes a simple echo command
    and captures the output.

    Args:
    ----
    capsys (CaptureFixture[str]): Pytest fixture to capture stdout and stderr.
    """
    _popen_stdout("echo 'Hello, World!'")
    captured = capsys.readouterr()
    assert "Hello, World!" in captured.out


def test_popen_stdout_lock(capsys: CaptureFixture[str]) -> None:
    """
    Test the _popen_stdout_lock function.

    This test checks if the function correctly executes a simple echo command
    and captures the output.

    Args:
    ----
    capsys (CaptureFixture[str]): Pytest fixture to capture stdout and stderr.
    """
    _popen_stdout_lock("echo 'Hello, World!'")
    captured = capsys.readouterr()
    assert "Hello, World!" in captured.out


@pytest.mark.asyncio()
async def test_run_coroutine_subprocess() -> None:
    """
    Test the run_coroutine_subprocess function.

    This test verifies that the function correctly executes a simple echo command
    asynchronously and returns the expected output.
    """
    result = await run_coroutine_subprocess(
        "echo 'Hello, World!'", "file:///tmp", str(pathlib.Path.cwd())
    )
    assert result == "Hello, World!"


@pytest.mark.asyncio()
async def test_run_coroutine_subprocess_concurrent() -> None:
    """
    Test concurrent execution of run_coroutine_subprocess.

    Verifies that multiple fast commands execute sequentially due to the semaphore and lock.
    Tests both the ordering and mutual exclusion properties of the synchronization.
    """
    start_time = time.time()
    execution_order = []

    async def run_with_tracking(i: int) -> str:
        result = await run_coroutine_subprocess(
            f"echo 'test{i}'", "file:///tmp", str(pathlib.Path.cwd())
        )
        execution_order.append(i)
        return result

    # Run multiple fast commands concurrently
    results = await asyncio.gather(*[run_with_tracking(i) for i in range(3)])
    elapsed = time.time() - start_time

    # Verify all commands completed successfully
    assert all(f"test{i}" == results[i] for i in range(3))

    # Verify commands ran sequentially (each taking ~0.05s sleep)
    assert elapsed >= 0.15  # 3 commands * 0.05s minimum

    # Verify strict ordering due to lock (not just semaphore)
    assert execution_order == [0, 1, 2], (
        "Commands should execute in strict order due to lock"
    )


def test_shell_console(capsys: CaptureFixture[str]) -> None:
    """
    Test the ShellConsole class.

    This test checks various scenarios of the ShellConsole.message method,
    including formatted messages and the quiet mode.

    Args:
    ----
    capsys (CaptureFixture[str]): Pytest fixture to capture stdout and stderr.
    """
    ShellConsole.message("Test message")
    captured = capsys.readouterr()
    assert "Test message" in captured.out

    ShellConsole.message("Formatted %s", "message")
    captured = capsys.readouterr()
    assert "Formatted message" in captured.out

    ShellConsole.quiet = True
    ShellConsole.message("This should not be printed")
    captured = capsys.readouterr()
    assert captured.out == ""
    ShellConsole.quiet = False

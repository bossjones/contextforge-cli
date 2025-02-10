---
description: Configuration and guidelines for pytest testing standards in ContextForge CLI
globs: ["**/*.py", "tests/**/*.py"]
---
You are a Python testing expert specializing in pytest who uses a systematic approach to test development and debugging for the ContextForge CLI project. Your expertise focuses on maintaining high-quality, type-safe, and well-documented tests.

## Core Testing Standards

1. Test Organization:
   - All tests must be in `./tests/` directory
   - Unit tests in `tests/unittests/`
   - Integration tests in `tests/integration/`
   - End-to-end tests in `tests/e2e/`
   - Performance tests in `tests/performance/`
   - CLI tests in `tests/cli/`
   - AI component tests in `tests/ai/`

2. Required Type Checking Imports:
   ```python
   from __future__ import annotations

   from typing import TYPE_CHECKING, Any, AsyncGenerator, Awaitable

   if TYPE_CHECKING:
       from _pytest.capture import CaptureFixture
       from _pytest.fixtures import FixtureRequest
       from _pytest.logging import LogCaptureFixture
       from _pytest.monkeypatch import MonkeyPatch
       from pytest_mock.plugin import MockerFixture
       from langchain.schema import BaseMessage
       from langchain.chains.base import Chain
       from langchain_core.runnables import RunnableConfig
   ```

## Analysis Pattern

When examining test failures, always follow this structured approach:

1. Error Analysis:
   - Extract and quote relevant error messages using <quote> tags
   - Include both the assertion failure and relevant context
   - Format quotes as:
   ```
   <quote>
   ```error message or relevant code```
   </quote>
   ```

2. Systematic Review:
   Use <thinking> tags to analyze the situation:
   ```
   <thinking>
   1. Current Implementation:
      - ✅/❌ What works/doesn't work
      - Current patterns used
      - Type safety analysis
      - Documentation completeness

   2. Similar Tests:
      - Patterns from related tests
      - Consistency with project standards
      - Fixture reuse opportunities

   3. Potential Issues:
      - Type safety concerns
      - Documentation gaps
      - Error handling weaknesses
      - Fixture conflicts

   4. Proposed Changes:
      - Specific changes needed
      - Expected outcomes
      - Type safety improvements
      - Documentation updates
   </thinking>
   ```

## Implementation Standards

1. Typing and Documentation:
   - Add typing annotations to ALL test functions
   - Include comprehensive docstrings following PEP 257
   - Use proper pytest fixtures and markers
   - Implement proper async testing patterns
   - Follow project's error handling patterns

2. Async Testing Patterns:
   ```python
   import pytest
   from typing import AsyncGenerator, AsyncIterator

   @pytest.fixture
   async def async_resource() -> AsyncGenerator[str, None]:
       """Provide an async resource for testing.

       Yields:
           str: The async resource.
       """
       # Setup
       resource = await setup_resource()
       yield resource
       # Cleanup
       await cleanup_resource(resource)

   @pytest.mark.asyncio
   async def test_async_function(async_resource: str) -> None:
       """Test async functionality.

       Args:
           async_resource: Async resource for testing.
       """
       result = await some_async_function(async_resource)
       assert result == expected_value
   ```

3. AI Component Testing:
   ```python
   from langchain.schema import BaseMessage
   from langchain.chains.base import Chain
   from langchain_core.runnables import RunnableConfig

   @pytest.fixture
   def mock_llm_chain(mocker: MockerFixture) -> Chain:
       """Create a mock LangChain chain.

       Args:
           mocker: Pytest mocker fixture.

       Returns:
           Chain: Mocked LangChain chain.
       """
       chain = mocker.Mock(spec=Chain)
       chain.invoke.return_value = {"output": "mocked response"}
       return chain

   async def test_ai_processing(
       mock_llm_chain: Chain,
       caplog: LogCaptureFixture,
   ) -> None:
       """Test AI processing logic.

       Args:
           mock_llm_chain: Mocked LangChain chain.
           caplog: Fixture to capture log messages.
       """
       result = await process_with_ai(mock_llm_chain)
       assert "AI processing complete" in caplog.text
   ```

4. CLI Testing Patterns:
   ```python
   from typer.testing import CliRunner
   from contextforge_cli.cli import app

   @pytest.fixture
   def cli_runner() -> CliRunner:
       """Provide a CLI runner for testing.

       Returns:
           CliRunner: The CLI test runner.
       """
       return CliRunner()

   def test_cli_command(
       cli_runner: CliRunner,
       tmp_path: Path,
   ) -> None:
       """Test CLI command execution.

       Args:
           cli_runner: CLI test runner.
           tmp_path: Temporary directory path.
       """
       result = cli_runner.invoke(app, ["command", "--arg", "value"])
       assert result.exit_code == 0
   ```

5. Structured Error Handling:
   ```python
   from contextforge_cli.exceptions import ValidationError

   def test_error_handling(caplog: LogCaptureFixture) -> None:
       """Test error handling patterns.

       Args:
           caplog: Fixture to capture log messages.
       """
       with pytest.raises(ValidationError) as exc_info:
           process_with_validation(invalid_data)

       assert "Validation failed" in str(exc_info.value)
       assert "error details" in caplog.text
   ```

## Test Execution

Always use UV for running tests. Example commands:
```bash
# Run a specific test with verbosity
uv run pytest -s --verbose --showlocals --tb=short tests/unittests/path/to/test.py::test_name

# Run tests matching a pattern
uv run pytest -v -k "test_pattern"

# Run with coverage
uv run pytest --cov=src/contextforge_cli --cov-report=term-missing tests/

# Debug with PDB
uv run pytest -s --pdb tests/unittests/path/to/test.py::test_name

# Run async tests
uv run pytest --asyncio-mode=auto tests/

# Run only AI component tests
uv run pytest tests/ai/

# Run with logging
uv run pytest --log-cli-level=DEBUG tests/
```

## Common Fixture Patterns

1. Resource Management:
```python
@pytest.fixture
async def managed_resource() -> AsyncGenerator[Resource, None]:
    """Provide a managed resource with proper cleanup.

    Yields:
        Resource: The managed resource.
    """
    resource = await Resource.create()
    yield resource
    await resource.cleanup()

@pytest.fixture
def mock_config(tmp_path: Path) -> Path:
    """Create a mock configuration file.

    Args:
        tmp_path: Temporary directory path.

    Returns:
        Path: Path to mock config file.
    """
    config_path = tmp_path / "config.yaml"
    config_path.write_text("key: value")
    return config_path
```

2. Mock Services:
```python
@pytest.fixture
def mock_api_client(mocker: MockerFixture) -> MagicMock:
    """Create a mock API client.

    Args:
        mocker: Pytest mocker fixture.

    Returns:
        MagicMock: Mocked API client.
    """
    client = mocker.Mock(spec=ApiClient)
    client.get.return_value = {"status": "success"}
    return client
```

## Maintenance Guidelines

1. Documentation:
   - Keep test docstrings up to date
   - Document fixture dependencies
   - Explain complex test scenarios
   - Update comments when modifying tests
   - Document test data and mocks

2. Error Handling:
   - Use appropriate pytest.raises contexts
   - Provide clear error messages
   - Handle async errors properly
   - Test both success and failure cases
   - Log relevant error details

3. Fixture Management:
   - Use descriptive fixture names
   - Avoid fixture name conflicts
   - Implement proper cleanup
   - Use appropriate fixture scopes
   - Share fixtures via conftest.py

4. Type Safety:
   - Maintain complete type annotations
   - Use proper generic types
   - Handle optional values correctly
   - Document type constraints
   - Use TypeVar for generic fixtures

Remember to:
- Follow the project's testing patterns consistently
- Ensure proper test isolation
- Implement thorough error handling
- Match implementation behavior exactly
- Use appropriate pytest plugins and markers
- Test async code with proper patterns
- Mock AI components appropriately
- Handle CLI testing edge cases

## Available Testing Tools and Plugins

1. Core Testing Frameworks:
   - `pytest`: Primary testing framework
   - `pytest-asyncio`: Async test support
   - `pytest-cov`: Coverage reporting
   - `pytest-mock`: Mocking support

2. HTTP Testing:
   - `pytest-aiohttp`: Testing aiohttp applications
   - `pytest-aioresponses`: Mock aiohttp requests
   - `pytest-httpx`: Mock httpx requests
   - `respx`: HTTP mocking for Python
   - `requests-mock`: Mock requests library

3. Performance and Debugging:
   - `pytest-memray`: Memory profiling
   - `pytest-skip-slow`: Skip slow tests
   - `pytest-retry`: Retry flaky tests
   - `pytest-ignore-flaky`: Handle flaky tests
   - `pyinstrument`: Python profiler

4. Test Organization and Reporting:
   - `pytest-clarity`: Improved test output
   - `pytest-sugar`: Progress visualization
   - `pytest-recording`: Record and replay HTTP interactions
   - `pytest-structlog`: Structured logging in tests

5. Time and State Management:
   - `pytest-freezegun`: Time freezing
   - `pytest-skipuntil`: Skip tests until a condition is met

6. Configuration Options:
   ```ini
   [tool.pytest.ini_options]
   asyncio_mode = "auto"
   testpaths = ["tests"]
   pythonpath = "."
   asyncio_default_fixture_loop_scope = "function"
   log_cli = false
   log_cli_level = "DEBUG"
   log_cli_format = "%(asctime)s [%(levelname)8s] [%(threadName)s] %(name)s - %(module)s.%(funcName)s (%(filename)s:%(lineno)d) - %(message)s"
   ```

7. Available Markers:
   - `@pytest.mark.cogs`: Tests utilizing cogs module
   - `@pytest.mark.e2e`: End-to-end tests
   - `@pytest.mark.integration`: Integration tests
   - `@pytest.mark.fast`: Fast tests
   - `@pytest.mark.slow`: Slow tests
   - `@pytest.mark.toolonly`: Custom Langchain tool tests
   - `@pytest.mark.unittest`: Unit tests
   - `@pytest.mark.asynciotyper`: Asyncio typer tests
   - `@pytest.mark.cli`: CLI tests
   - `@pytest.mark.agenticonly`: Agentic module tests

8. Common Test Commands:
   ```bash
   # Run tests with specific marker
   uv run pytest -v -m "fast"

   # Run tests with coverage and specific marker
   uv run pytest --cov=src/contextforge_cli --cov-report=term-missing -m "not slow"

   # Run tests with logging
   uv run pytest --log-cli-level=DEBUG -v tests/

   # Run tests with retry for flaky tests
   uv run pytest --reruns 3 --reruns-delay 1

   # Run tests with memory profiling
   uv run pytest --memray tests/

   # Run only async tests
   uv run pytest -m "asynciotyper" --asyncio-mode=auto tests/
   ```

Remember to:
- Use appropriate markers to categorize tests
- Leverage the right plugins for specific testing needs
- Configure logging appropriately for debugging
- Use memory profiling for performance testing
- Handle flaky tests with retry mechanisms
- Mock external services appropriately

## Linting Standards and Commands

1. CI Linting:
   ```bash
   # Run pylint with CI configuration
   uv run pylint --output-format=colorized --disable=all --max-line-length=120 --enable=F,E --rcfile pyproject.toml src/contextforge_cli tests
   ```

2. Linting Configuration:
   - Use `pyproject.toml` for pylint configuration
   - Enable only errors (E) and fatal errors (F)
   - Set max line length to 120 characters
   - Apply to both source code and tests
   - Use colorized output for better readability

3. Common Linting Patterns:
   ```bash
   # Lint specific file
   uv run pylint --output-format=colorized --disable=all --max-line-length=120 --enable=F,E --rcfile pyproject.toml src/contextforge_cli/specific_file.py

   # Lint specific test file
   uv run pylint --output-format=colorized --disable=all --max-line-length=120 --enable=F,E --rcfile pyproject.toml tests/unittests/test_specific.py

   # Lint with detailed output
   uv run pylint --output-format=parseable --disable=all --max-line-length=120 --enable=F,E --rcfile pyproject.toml src/contextforge_cli tests

   # Lint and generate report
   uv run pylint --output-format=json --disable=all --max-line-length=120 --enable=F,E --rcfile pyproject.toml src/contextforge_cli tests > pylint-report.json
   ```

4. Pre-commit Integration:
   ```yaml
   # In .pre-commit-config.yaml
   - repo: local
     hooks:
       - id: pylint
         name: pylint
         entry: uv run pylint
         language: system
         types: [python]
         args: [
           "--output-format=colorized",
           "--disable=all",
           "--max-line-length=120",
           "--enable=F,E",
           "--rcfile=pyproject.toml"
         ]
   ```

5. Error Categories:
   - F: Fatal errors that prevent pylint from running
   - E: Error for important programming issues

   Common error codes:
   - E0001: Syntax error
   - E0100: __init__ method is a generator
   - E0101: Explicit return in __init__
   - E0102: Function/class/method already defined
   - E0103: Break/continue outside loop
   - E0104: Return outside function
   - E0105: Yield outside function
   - E0108: Duplicate argument name
   - E0110: Abstract class with abstract methods instantiated
   - E0111: Assignment to function call that doesn't return
   - E0112: More than one starred expression in assignment
   - E0113: Starred assignment target must be in a list or tuple
   - E0114: Can use starred expression only in assignment target
   - E0115: Name mandatory arguments before variable arguments
   - E0116: Continue not supported inside finally clause
   - E0117: nonlocal declaration not allowed at module level
   - E0118: Name referenced before global declaration

Remember to:
- Run linting as part of CI pipeline
- Fix all fatal (F) and error (E) level issues
- Keep configuration in pyproject.toml
- Use pre-commit hooks for local development
- Generate reports for tracking improvements

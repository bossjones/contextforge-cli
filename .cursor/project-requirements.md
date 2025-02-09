# ContextForge CLI Project Requirements

## Project Overview
ContextForge CLI is an async-first command-line tool focused on AI/ML integration through LangChain and LangGraph. The project emphasizes modern Python practices, strong typing, and comprehensive testing.

## Technical Requirements

### Core Technologies
- Python 3.11+
- UV for dependency management
- AsyncTyperImproved for CLI implementation
- LangChain and LangGraph for AI/ML workflows
- Structlog for logging
- Pytest for testing

### Key Features
1. **Async-First Design**
   - Consistent use of async/await patterns
   - Proper async context managers
   - Efficient async file operations with aiofiles
   - Proper cancellation handling

2. **AI/ML Integration**
   - LangChain for structured AI/ML workflows
   - LangGraph for complex agent systems
   - Proper error handling for API calls
   - Streaming response support
   - Rate limit handling

3. **CLI Implementation**
   - Typer/AsyncTyperImproved for command structure
   - Rich for console output
   - Proper signal handling
   - Dynamic subcommand loading

4. **Logging and Monitoring**
   - Structured logging with structlog
   - Contextual error tracking
   - Request correlation
   - Performance monitoring

### Dependency Management
- UV as primary dependency management tool
- Lock file consistency with `uv.lock`
- Specific version constraints in pyproject.toml
- Regular dependency updates with `uv lock --upgrade`

### Development Tools
- Ruff for linting and formatting
- Mypy for type checking
- Pre-commit hooks for code quality
- VCR.py for HTTP interaction testing

## Code Quality Standards

### Type Safety
- Strict typing for all functions and classes
- Return type annotations required
- Proper use of TypeVar and ParamSpec
- Runtime type checking where necessary

### Documentation
- Google-style docstrings (PEP 257)
- Type information in docstrings
- Usage examples for complex functions
- Comprehensive module documentation

### Error Handling
- Custom exception hierarchies
- Contextual error messages
- Proper error recovery strategies
- Error boundaries at system boundaries

### Logging
- Structured logging with structlog
- Proper log levels
- Contextual data in log events
- Correlation IDs for request tracing

## Testing Standards

### Test Organization
- All tests in `./tests/` directory
- Proper test categorization with pytest markers
- Mirror source code directory structure in tests
- Include `__init__.py` in all test directories

### Test Types
1. **Unit Tests**
   - Located in `tests/unittests/`
   - Test individual components in isolation
   - Use appropriate mocking
   - Focus on edge cases

2. **Integration Tests**
   - Located in `tests/integration/`
   - Test component interactions
   - Use VCR.py for HTTP interactions
   - Test real-world scenarios

### Test Requirements
- Use pytest exclusively (no unittest)
- Full type annotations for all tests
- Comprehensive docstrings
- Use pytest fixtures for reusable components
- Include TYPE_CHECKING imports:
  ```python
  if TYPE_CHECKING:
      from _pytest.capture import CaptureFixture
      from _pytest.fixtures import FixtureRequest
      from _pytest.logging import LogCaptureFixture
      from _pytest.monkeypatch import MonkeyPatch
      from pytest_mock.plugin import MockerFixture
  ```

### Test Best Practices
- Use `tmp_path` fixture for file operations
- Implement proper cleanup in fixtures
- Use structlog's capture_logs for log testing
- Never use pytest's caplog for structlog testing
- Mark tests appropriately (e.g., `@pytest.mark.asyncio`)

## Project Structure
```
src/contextforge_cli/
├── __init__.py
├── __main__.py
├── __version__.py
├── bot_logger/          # Logging components
├── models/             # Data models
├── shell/             # Shell interaction components
├── subcommands/       # CLI subcommand implementations
├── utils/             # Utility functions and helpers
├── vendored/          # Vendored dependencies
└── cli.py            # Main CLI entry point

tests/
├── __init__.py
├── conftest.py       # Shared fixtures
├── unittests/        # Unit tests
└── integration/      # Integration tests
```

## Development Workflow

### Setup and Installation
1. Use UV for dependency management:
   ```bash
   uv sync --all-extras --dev
   ```

2. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Development Process
1. **Code Quality**
   - Run Ruff for linting and formatting
   - Use mypy for type checking
   - Follow import standards
   - Maintain docstring quality

2. **Testing**
   - Write tests before implementation
   - Run specific tests during development:
     ```bash
     uv run pytest -v path/to/test.py
     ```
   - Run full test suite before commits

3. **Version Control**
   - Use semantic commit messages
   - Keep commits focused and atomic
   - Reference issues in commits
   - Follow branch naming conventions

4. **Documentation**
   - Update docstrings as code changes
   - Keep README.md current
   - Document breaking changes
   - Include examples for complex features

### Dependency Updates
- Regular dependency checks with `uv lock --check`
- Controlled updates with `uv lock --upgrade`
- Test suite verification after updates
- Lock file maintenance

## Import Standards

### Organization
- Place `from __future__ import annotations` at the top of every Python file
- Group imports into sections separated by a blank line:
  1. Future imports
  2. Standard library imports
  3. Third-party imports
  4. Local imports from contextforge_cli
  5. Type checking imports (if needed)
- Sort imports alphabetically within each section
- Use absolute imports instead of relative imports

### Linter Directives
Add appropriate linter directives at the top of files based on imports:
- For Discord.py files:
  ```python
  # pylint: disable=no-member
  # pyright: reportAttributeAccessIssue=false
  ```
- For Pydantic files:
  ```python
  # pylint: disable=no-name-in-module
  # pylint: disable=no-member
  # pyright: reportInvalidTypeForm=false
  # pyright: reportUndefinedVariable=false
  ```

### Best Practices
- Use consistent import aliases across the codebase
- Import only what is needed, avoid wildcard imports (*)
- Use multi-line imports for better readability
- Keep import blocks organized and clean with proper spacing

### Example
```python
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

import structlog
import typer
from rich import print as rprint
from rich.console import Console

from contextforge_cli.bot_logger import configure_logging
from contextforge_cli.shell import ProcessException, ShellConsole

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
```

## CLI Implementation Standards

### Core Structure
- Use AsyncTyperImproved for async support
- Initialize main APP with proper configuration
- Load subcommands dynamically
- Place subcommands in dedicated directory

### Command Organization
- Place all subcommands in `subcommands/` directory
- Use `_cmd.py` suffix for command files
- Each subcommand module defines its own APP instance
- Follow consistent naming patterns

### Command Implementation
- Use proper type annotations for all parameters
- Include descriptive docstrings
- Use Annotated for command parameters
- Implement proper signal handling
- Use rich for console output

### Example
```python
from typing import Annotated
import typer
from rich import print as rprint

APP = typer.Typer()

@APP.command()
def my_command(
    param: Annotated[str, typer.Option("--param", "-p", help="Parameter description")] = "default",
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed output")] = False,
) -> None:
    """Command description following Google style.

    Args:
        param: Parameter description
        verbose: Whether to show detailed output
    """
    if verbose:
        rprint(f"[green]Running command with param: {param}[/green]")
    # Command implementation
```

## AI Integration Standards

### LangChain Integration
- Use LangChain for structured AI/ML workflows
- Implement proper error handling for API calls
- Use streaming responses when appropriate
- Handle rate limits and quotas
- Implement retry logic for API failures

### LangGraph Integration
- Follow LangGraph's component structure
- Use proper state management in graph nodes
- Implement proper error handling in graph edges
- Create reusable graph components
- Use appropriate markers for graph-based tests

### Best Practices
1. **Error Handling**
   - Implement proper retries for LLM calls
   - Use streaming for long-running operations
   - Implement proper memory management
   - Handle rate limits through configurable mechanisms

2. **State Management**
   - Use typed dictionaries for agent states
   - Implement proper memory handling
   - Use proper annotations for all functions
   - Handle side effects appropriately

3. **Testing**
   - Mark tests with @pytest.mark.vcr
   - Configure VCR.py properly
   - Implement proper mocking
   - Test error scenarios

### Example
```python
from typing import Dict, List, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph

class AgentState(TypedDict):
    """Type definition for agent state."""
    messages: List[BaseMessage]
    next_step: str
    memory: Dict[str, Any]

async def create_agent_workflow(tools: List[BaseTool]) -> StateGraph:
    """Create a workflow graph for an AI agent system.

    Args:
        tools: List of tools available to the agent

    Returns:
        StateGraph: A configured workflow graph
    """
    workflow = StateGraph(AgentState)
    # Workflow configuration
    return workflow.compile()
```

## Architecture Guidelines

### 1. Modular Structure
```
src/
├── app/               # Next.js app router
├── components/        # Reusable UI components
│   ├── core/          # Base components (buttons, inputs)
│   ├── accounting/    # Domain-specific components
│   └── shared/       # Cross-feature components
├── lib/
│   ├── api/           # API clients
│   ├── hooks/         # Custom hooks
│   ├── utils/         # Helper functions
│   └── validation/    # Zod schemas
├── types/             # Global TS types
```

### 2. Server/Client Separation
- **Server Components**: Default to server components for:
  - Data fetching
  - Sensitive operations
  - Static content
- **Client Components**: Only use when needed for:
  - Interactivity
  - Browser APIs
  - State management

### 3. Reusable Components
1. Create atomic components with:
   - PropTypes using TypeScript interfaces
   - Storybook stories for documentation
   - Accessibility attributes by default
2. Follow naming convention:
   - `FeatureComponentName.tsx` (e.g. `DepreciationCalculator.tsx`)
   - `CoreComponentName.tsx` (e.g. `FormInput.tsx`)

### 4. API Design Rules
- Versioned endpoints: `/api/v1/...`
- RESTful structure for resources
- Error format standardization:
  ```ts
  interface APIError {
    code: string;
    message: string;
    details?: Record<string, unknown>;
  }
  ```

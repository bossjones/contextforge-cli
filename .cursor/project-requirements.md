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

5. **Cursor Rules Migration**
   - Intelligent parsing of .cursorrules and cursorrules.xml files
   - Chain of Thought processing for content analysis
   - Draft generation in prompts/drafts directory
   - Iterative refinement process
   - Safe migration to .cursor/rules/*.mdc
   - Content validation and verification
   - Comprehensive logging of migration process
   - Rollback capabilities for failed migrations
   - Support for incremental migrations
   - Progress tracking and reporting

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
│   ├── __init__.py
│   ├── formatters.py
│   └── handlers.py
├── models/             # Data models and schemas
│   ├── __init__.py
│   ├── base.py
│   └── types.py
├── shell/             # Shell interaction components
│   ├── __init__.py
│   ├── commands.py
│   └── processors.py
├── subcommands/       # CLI subcommand implementations
│   ├── __init__.py
│   ├── migrate_rules/
│   │   ├── __init__.py
│   │   ├── parser.py
│   │   └── validator.py
│   └── base.py
├── utils/             # Utility functions and helpers
│   ├── __init__.py
│   ├── async_helpers.py
│   └── file_ops.py
├── vendored/          # Vendored dependencies
│   └── __init__.py
└── cli.py            # Main CLI entry point

tests/
├── __init__.py
├── conftest.py       # Shared test fixtures
├── unittests/        # Unit tests
│   ├── __init__.py
│   └── utils/
└── integration/      # Integration tests
    └── __init__.py

docs/
├── architecture/     # Architecture documentation
├── api/             # API documentation
├── examples/        # Usage examples
└── phases/          # Phase completion docs

.cursor/
├── rules/           # MDC rule files
└── memories/        # Memory system files
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

## Project Roadmap (Updated Implementation Sequence)

### Phase 1: Core Framework and Basic Functionality

1. Implement Cursor Rules Migration System
   - [ ] Design Chain of Thought processing system for rule analysis
   - [ ] Create parser for .cursorrules and cursorrules.xml files
   - [ ] Implement draft generation in prompts/drafts directory
   - [ ] Develop iterative refinement workflow
   - [ ] Build safe migration system to .cursor/rules/*.mdc
   - [ ] Implement validation and verification
   - [ ] Add comprehensive logging
   - [ ] Create rollback mechanism
   - [ ] Support incremental migrations
   - [ ] Add progress tracking and reporting

2. Set up project structure
   - [ ] Initialize Git repository
   - [ ] Create virtual environment
   - [ ] Set up project dependencies (Typer, yt-dlp, etc.)

3. Implement basic CLI structure using Typer
   - [ ] Create main CLI entry point
   - [ ] Implement basic error handling and logging

4. Develop template generation feature
   - [ ] Create command to generate .cursor/rules/*.mdc files from a template
   - [ ] Implement file reading and writing functionality
   - [ ] Add error handling for file operations

5. Implement LLM integration for feature planning
   - [ ] Set up LLM API connection (e.g., OpenAI GPT)
   - [ ] Create command to generate detailed story list for a given feature
   - [ ] Implement prompt engineering for effective LLM interaction

### Phase 2: YouTube Integration and Subtitle Processing

6. Integrate yt-dlp for YouTube video processing
   - [ ] Implement YouTube video URL parsing
   - [ ] Create command to download subtitles using yt-dlp

7. Develop subtitle summarization feature
   - [ ] Implement text processing for subtitle content
   - [ ] Create summarization algorithm or integrate with LLM for summarization
   - [ ] Implement highlighting of important concepts

### Phase 3: Advanced Context Management

8. Implement dual-mode operation system (Plan/Act)
   - [ ] Design and implement Plan mode functionality
   - [ ] Design and implement Act mode functionality
   - [ ] Create seamless switching between modes

9. Develop confidence scoring system
   - [ ] Design confidence scoring algorithm
   - [ ] Integrate confidence scoring into Plan/Act modes
   - [ ] Implement feedback loop for improving confidence scores

### Phase 4: Memory Systems and Documentation

10. Implement advanced memory systems
    - [ ] Design and implement short-term memory functionality
    - [ ] Design and implement long-term memory functionality
    - [ ] Create memory management commands

11. Develop automated documentation capabilities
    - [ ] Implement code analysis for documentation generation
    - [ ] Create command to generate project documentation
    - [ ] Implement documentation update functionality

### Phase 5: Integration and Polish

12. Integrate all components into a cohesive system
    - [ ] Ensure smooth interaction between all features
    - [ ] Implement comprehensive error handling and logging

13. Develop user configuration system
    - [ ] Create configuration file structure
    - [ ] Implement command to manage user preferences

14. Create comprehensive test suite
    - [ ] Implement unit tests for all major components
    - [ ] Create integration tests for end-to-end functionality

15. Polish user experience
    - [ ] Refine CLI interface and command structure
    - [ ] Implement progress bars and rich console output
    - [ ] Create detailed help documentation for all commands

### Phase 6: Expansion and Advanced Features

16. Implement plugin system for extensibility
    - [ ] Design plugin architecture
    - [ ] Create sample plugins to demonstrate functionality

17. Develop AI context enhancement features
    - [ ] Implement advanced context analysis
    - [ ] Create commands for context manipulation and optimization

18. Integrate with version control systems
    - [ ] Implement Git integration for context tracking
    - [ ] Create commands for managing context across branches

## Architecture Guidelines

### 1. Modular Structure
```
src/contextforge_cli/
├── __init__.py
├── __main__.py
├── __version__.py
├── bot_logger/          # Logging components
│   ├── __init__.py
│   ├── formatters.py
│   └── handlers.py
├── models/             # Data models and schemas
│   ├── __init__.py
│   ├── base.py
│   └── types.py
├── shell/             # Shell interaction components
│   ├── __init__.py
│   ├── commands.py
│   └── processors.py
├── subcommands/       # CLI subcommand implementations
│   ├── __init__.py
│   ├── migrate_rules/
│   │   ├── __init__.py
│   │   ├── parser.py
│   │   └── validator.py
│   └── base.py
├── utils/             # Utility functions and helpers
│   ├── __init__.py
│   ├── async_helpers.py
│   └── file_ops.py
├── vendored/          # Vendored dependencies
│   └── __init__.py
└── cli.py            # Main CLI entry point

tests/
├── __init__.py
├── conftest.py       # Shared test fixtures
├── unittests/        # Unit tests
│   ├── __init__.py
│   └── utils/
└── integration/      # Integration tests
    └── __init__.py

docs/
├── architecture/     # Architecture documentation
├── api/             # API documentation
├── examples/        # Usage examples
└── phases/          # Phase completion docs

.cursor/
├── rules/           # MDC rule files
└── memories/        # Memory system files
```

### 2. Component Organization

1. **Core Components**
   - `bot_logger/`: Structured logging with contextual tracking
   - `models/`: Pydantic models and type definitions
   - `shell/`: Async shell interaction handlers
   - `subcommands/`: CLI command implementations
   - `utils/`: Shared utility functions

2. **Testing Structure**
   - Mirror source directory structure in tests
   - Separate unit and integration tests
   - Shared fixtures in conftest.py
   - VCR.py cassettes for HTTP tests

3. **Documentation Organization**
   - Architecture docs in docs/architecture/
   - API documentation with examples
   - Phase completion records
   - MDC rules in .cursor/rules/

### 3. Design Patterns

1. **Async Patterns**
   - Consistent use of async/await
   - Proper context managers
   - Efficient async file operations
   - Cancellation handling

2. **AI/ML Integration**
   - LangChain workflows
   - LangGraph agent systems
   - Streaming response handling
   - Rate limit management

3. **Error Handling**
   - Custom exception hierarchies
   - Contextual error messages
   - Proper recovery strategies
   - Error boundaries

### 4. File Standards

1. **Python Files**
   - Future imports at top
   - Organized import sections
   - Google-style docstrings
   - Type annotations
   - Proper error handling

2. **MDC Files**
   - Clear frontmatter
   - Proper metadata annotations
   - Structured content sections
   - Implementation examples

3. **Documentation Files**
   - Clear hierarchical structure
   - Practical examples
   - Type information
   - Error cases
   - Usage patterns

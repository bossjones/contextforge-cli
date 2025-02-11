# ContextForge CLI Development Standards

## Purpose
You are an AI assistant responsible for helping a developer maintain Python code quality and develop an async-first CLI tool using modern Python practices, with a focus on AI/ML integration through LangChain and LangGraph.

## Core Instructions
1. Follow the established project structure with `src/contextforge_cli` as the main package
2. Maintain separation of concerns between different modules and components
3. Use UV (https://docs.astral.sh/uv) for dependency management and virtual environments
4. Follow the established directory structure for tests, documentation, and source code
5. Ensure all new code follows the project's typing and documentation standards
6. Implement async-first design patterns throughout the codebase
7. Utilize LangChain and LangGraph for AI/ML integrations
8. During development, maintain notes of reusable components in the `Lessons` section (`@lessons-learned.md`) file so that you will not make the same mistake again.
9. Use the `Scratchpad` at `@scratchpad.md` file to organize thoughts and track progress.

## Using the Scratchpad

Especially when you receive a new task, you should first review the content of the Scratchpad, clear old different task if necessary, first explain the task, and plan the steps you need to take to complete the task. You can use todo markers to indicate the progress, e.g.
[X] Task 1
[ ] Task 2

Also update the progress of the task in the Scratchpad when you finish a subtask.
Especially when you finished a milestone, it will help to improve your depth of task accomplishment to use the Scratchpad to reflect and plan.
The goal is to help you maintain a big picture as well as the progress of the task. Always refer to the Scratchpad when you plan the next step.

# Tools

If you need to use llm from this repo, you can refer to @devin-persona.mdc or @devin-multi-agent-persona.mdc for the commands.


## Project Structure Standards
- Maintain clear project structure:
  - `src/contextforge_cli/`: Main package directory
  - `tests/`: Test directory
  - `docs/`: Documentation
  - `scripts/`: Utility scripts
  - `hack/`: IDE and tool configurations
- Keep configuration files in root directory (pyproject.toml, tox.ini, mypy.ini)
- Use modular design with distinct files for models, services, controllers, utilities
- Follow composition over inheritance principle
- Use design patterns like Adapter, Decorator, and Bridge when appropriate
- Keep vendored code in `src/contextforge_cli/vendored/` directory

## Python Code Standards
1. **Type Safety**
   - Add typing annotations to ALL functions and classes with return types
   - Use TypeVar and ParamSpec for generic types
   - Add runtime type checking where necessary
   - Use Literal types for constrained values

2. **Documentation**
   - Include PEP 257-compliant docstrings in Google style for all functions and classes
   - Add detailed comments for complex logic
   - Provide rich error context for debugging
   - Follow DRY and KISS principles

3. **Async Programming**
   - Use async/await patterns consistently
   - Implement proper async context managers
   - Use aiofiles for all file operations
   - Use asyncio.gather for concurrent operations
   - Implement proper cancellation handling
   - Use AsyncTyperImproved for CLI commands

4. **Error Handling**
   - Define custom exception hierarchies
   - Use contextual error messages with structured data
   - Implement proper error recovery strategies
   - Add error boundaries at system boundaries

5. **Logging**
   - Use structlog for all logging operations
   - Include contextual data in log events
   - Use proper log levels consistently
   - Add correlation IDs for request tracing

## Testing Standards
1. **Test Organization**
   - Place all tests in `./tests/` directory
   - Use pytest exclusively (no unittest module)
   - Add type annotations and docstrings to all tests
   - Use pytest markers for categorization
   - Mirror source code directory structure in tests

2. **Test Types**
   - Unit tests in `tests/unittests/`
   - Integration tests in `tests/integration/`
   - End-to-end tests in `tests/e2e/`
   - Performance tests in `tests/performance/`

3. **Test Requirements**
   - Import TYPE_CHECKING block with pytest types:
     ```python
     if TYPE_CHECKING:
         from _pytest.capture import CaptureFixture
         from _pytest.fixtures import FixtureRequest
         from _pytest.logging import LogCaptureFixture
         from _pytest.monkeypatch import MonkeyPatch
         from pytest_mock.plugin import MockerFixture
     ```
   - Use pytest fixtures for reusable components
   - Use tmp_path fixture for file-based tests
   - Use VCR.py for recording and replaying HTTP interactions

## AI Integration Standards
1. **LangChain Usage**
   - Use LangChain for structured AI/ML workflows
   - Implement proper error handling for LLM calls
   - Use streaming responses when appropriate
   - Handle rate limits and quotas properly

2. **LangGraph Implementation**
   - Follow LangGraph's component structure
   - Use proper state management in graph nodes
   - Implement proper error handling in edges
   - Create reusable graph components

## Documentation Standards
1. **Code Documentation**
   - Add comprehensive docstrings to all code
   - Include type information in docstrings
   - Document exceptions and error conditions
   - Add usage examples for complex functions

2. **Project Documentation**
   - Maintain README.md with project overview
   - Keep ARCHITECTURE.md updated
   - Update CHANGELOG.md for all changes
   - Document API endpoints and schemas

3. **Comments**
   - Never remove existing comments
   - Add descriptive inline comments
   - Update comments when code changes
   - Cross-reference related documentation

## Import Standards
1. **Import Organization**
   - Place `from __future__ import annotations` at top
   - Group imports by section:
     1. Future imports
     2. Standard library imports
     3. Third-party imports
     4. Local imports
     5. Type checking imports
   - Sort imports alphabetically within sections
   - Use absolute imports over relative imports
   - NEVER use relative imports (no .. or . notation)

2. **Import Rules**
   - Add appropriate linter directives for imports
   - Use consistent import aliases
   - Import only what is needed
   - Keep import blocks organized and clean
   - Always use full package path from root for local imports
     Example:
     ```python
     # Correct
     from contextforge_cli.subcommands.migrate_rules.models.validation import ValidationResult

     # Incorrect
     from ..models.validation import ValidationResult  # No relative imports
     from .base import BaseValidator  # No relative imports
     ```
   - For TYPE_CHECKING imports, also use absolute imports:
     ```python
     if TYPE_CHECKING:
         from contextforge_cli.subcommands.migrate_rules.models.context import MDCContext
     ```

3. **Import Structure**
   - Keep imports grouped by their source:
     ```python
     from __future__ import annotations  # Future imports first

     import abc  # Standard library imports
     import asyncio
     from typing import Optional, List

     import structlog  # Third-party imports
     from pydantic import BaseModel

     from contextforge_cli.models import SomeModel  # Local imports
     from contextforge_cli.utils import some_util

     if TYPE_CHECKING:  # Type checking imports last
         from contextforge_cli.types import SomeType
     ```

## Tool Configuration Standards
1. **Ruff Configuration**
   - Document all rules in pyproject.toml
   - Use per-file-ignores for exceptions
   - Run Ruff with --fix for auto-fixes
   - Keep line length consistent

2. **UV Usage**
   - Use `uv sync` for dependency installation
   - Maintain lock file consistency
   - Use `uv.lock` for deterministic resolution
   - Document dependencies in pyproject.toml

## Memory Management
- Update `@memories.md` for all interactions
- Document lessons learned in `@lessons-learned.md`
- Use `.cursor-scratchpad` for task tracking
- Cross-reference between memory files

## Version Control Standards
1. **Commit Messages**
   - Use conventional commit format:
     - fix: For bug fixes
     - feat: For new features
     - docs: For documentation
     - style: For formatting
     - refactor: For refactoring
     - test: For adding tests
     - chore: For maintenance
   - Keep messages clear and descriptive
   - Reference issues when applicable

2. **Branch Management**
   - Use feature branches for development
   - Keep main/master branch stable
   - Delete branches after merging
   - Use meaningful branch names

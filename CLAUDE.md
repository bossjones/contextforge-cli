# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Development Guidelines

This document contains critical information about working with this codebase. Follow these guidelines precisely.

# Architecture Overview

ContextForge CLI is a Python-based tool for managing and enhancing AI context in projects. Key architectural components:

## Core Architecture
- **CLI Framework**: Typer with AsyncTyper extension for async command support
- **AI Integration**: LangChain/LangGraph for advanced AI workflows
- **Context Management**: Memory system with @memories.md, @lessons-learned.md, @scratchpad.md
- **Dual-Mode System**: Plan mode (analysis) → Act mode (implementation) with confidence scoring
- **Multi-Agent Architecture**: Coordinated planning and execution agents

## Key Directories
- `src/contextforge_cli/`: Main package with CLI, models, utils, subcommands
- `src/contextforge_cli/subcommands/`: CLI subcommands (ai_docs_cmd, migrate_rules, etc.)
- `src/contextforge_cli/utils/`: Utility modules (file operations, AI docs, shell helpers)
- `src/contextforge_cli/models/`: Data models and validation
- `src/contextforge_cli/vendored/`: Third-party code (cursorfocus integration)
- `.cursor/rules/`: Cursor IDE rules and conventions

## Common Commands

### Development
- Build: `uv run python -m build` or `make build`
- Format: `uv run ruff format .`
- Lint: `uv run ruff check . --fix`
- Type check: `uv run pyright`
- Test: `uv run pytest` or `make test`
- Install: `uv sync` or `make install`

### Project Scripts
- `cfctl` or `contextforgectl`: Main CLI entry points
- Script commands available in pyproject.toml [project.scripts]

## Core Development Rules

1. Package Management
   - ONLY use uv, NEVER pip
   - Installation: `uv add package`
   - Running tools: `uv run tool`
   - Upgrading: `uv add --dev package --upgrade-package package`
   - FORBIDDEN: `uv pip install`, `@latest` syntax

2. Code Quality
   - Type hints required for all code
   - Public APIs must have docstrings
   - Functions must be focused and small
   - Follow existing patterns exactly
   - Line length: 88 chars maximum

3. Testing Requirements
   - Framework: `uv run pytest`
   - Async testing: use anyio, not asyncio
   - Coverage: test edge cases and errors
   - New features require tests
   - Bug fixes require regression tests

- For commits fixing bugs or adding features based on user reports add:
  ```bash
  git commit --trailer "Reported-by:<name>"
  ```
  Where `<name>` is the name of the user.

- For commits related to a Github issue, add
  ```bash
  git commit --trailer "Github-Issue:#<number>"
  ```
- NEVER ever mention a `co-authored-by` or similar aspects. In particular, never
  mention the tool used to create the commit message or PR.

## Pull Requests

- Create a detailed message of what changed. Focus on the high level description of
  the problem it tries to solve, and how it is solved. Don't go into the specifics of the
  code unless it adds clarity.

- Always add `jerome3o-anthropic` and `jspahrsummers` as reviewer.

- NEVER ever mention a `co-authored-by` or similar aspects. In particular, never
  mention the tool used to create the commit message or PR.

## Python Tools

## Code Formatting

1. Ruff
   - Format: `uv run ruff format .`
   - Check: `uv run ruff check .`
   - Fix: `uv run ruff check . --fix`
   - Critical issues:
     - Line length (88 chars)
     - Import sorting (I001)
     - Unused imports
   - Line wrapping:
     - Strings: use parentheses
     - Function calls: multi-line with proper indent
     - Imports: split into multiple lines

2. Type Checking
   - Tool: `uv run pyright`
   - Requirements:
     - Explicit None checks for Optional
     - Type narrowing for strings
     - Version warnings can be ignored if checks pass

3. Pre-commit
   - Config: `.pre-commit-config.yaml`
   - Runs: on git commit
   - Tools: Prettier (YAML/JSON), Ruff (Python)
   - Ruff updates:
     - Check PyPI versions
     - Update config rev
     - Commit config first

## Error Resolution

1. CI Failures
   - Fix order:
     1. Formatting
     2. Type errors
     3. Linting
   - Type errors:
     - Get full line context
     - Check Optional types
     - Add type narrowing
     - Verify function signatures

2. Common Issues
   - Line length:
     - Break strings with parentheses
     - Multi-line function calls
     - Split imports
   - Types:
     - Add None checks
     - Narrow string types
     - Match existing patterns

3. Best Practices
   - Check git status before commits
   - Run formatters before type checks
   - Keep changes minimal
   - Follow existing patterns
   - Document public APIs
   - Test thoroughly

# Context Management System

This project uses a sophisticated context management system with specific files:

## Memory Files
- `@memories.md`: Chronological log of all interactions and decisions
- `@lessons-learned.md`: Knowledge base for preventing mistakes and capturing solutions
- `@scratchpad.md`: Phase-specific task tracker and implementation planner

## Cursor Rules Integration
- `.cursor/rules/`: Contains project-specific Cursor IDE rules
- Key rules include memory management, conventional commits, and documentation standards
- Always reference brain-memories-lessons-learned-scratchpad.mdc.md for context patterns

## Mode System
1. **Plan Mode**: Analysis phase with confidence scoring (requires 95% confidence to proceed)
2. **Act Mode**: Implementation phase triggered after sufficient confidence
3. **Multi-Agent Coordination**: Through scratchpad system for task management

# Important Patterns

## AsyncTyper Usage
- Project uses custom AsyncTyper extension for async CLI commands
- Located in `src/contextforge_cli/asynctyper.py`
- Supports both sync and async command patterns

## Dependency Management
- Heavy use of LangChain ecosystem (langchain, langgraph, langsmith)
- AI/ML tools: sentence-transformers, mlx-whisper, pytorch vision
- Testing: extensive pytest setup with multiple markers and async support
- Development: ruff for linting/formatting, pyright for type checking

## Testing Structure
- Comprehensive test markers system (see pyproject.toml)
- Async testing with anyio (not asyncio)
- Coverage reporting with multiple formats
- Integration and unit test separation

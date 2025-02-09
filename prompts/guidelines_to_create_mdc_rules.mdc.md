---
description: Guidelines and best practices for creating .mdc (Markdown Configuration) files in Cursor for Python projects, including structure, metadata annotations, and formatting rules
globs: ["**/*.mdc"]
---

# Cursor MDC File Guidelines for Python

@context {
    "type": "documentation",
    "purpose": "cursor_rules",
    "format_version": "1.0.0",
    "supported_content_types": [
        "guidelines",
        "api_docs",
        "examples",
        "implementations"
    ],
    "language": "python",
    "python_version": ">=3.8",
    "recommended_tools": [
        "ruff",
        "mypy",
        "pytest",
        "black",
        "isort"
    ],
    "model_compatibility": {
        "primary": "anthropic",
        "models": ["claude-3-opus", "claude-3-sonnet", "claude-2.1"],
        "markup": "xml_enhanced"
    }
}

@structure {
    "required_sections": [
        "frontmatter",
        "title",
        "context",
        "content_sections"
    ],
    "optional_sections": [
        "version",
        "last_updated",
        "examples",
        "implementations",
        "related_files"
    ],
    "recommended_sections": [
        "practical_examples",
        "common_patterns",
        "type_definitions",
        "docstring_format",
        "async_patterns",
        "error_handling",
        "testing_guidelines",
        "dependency_management"
    ]
}

## File Structure

### 1. Frontmatter

@frontmatter_rules [
    {
        "id": "position",
        "rule": "Must be at the very top of the file",
        "severity": "error"
    },
    {
        "id": "description",
        "rule": "Single sentence, clear purpose",
        "severity": "error"
    },
    {
        "id": "globs",
        "rule": "Array of relevant file patterns",
        "severity": "error"
    },
    {
        "id": "related_docs",
        "rule": "Optional array of related documentation files - MUST only reference existing files",
        "severity": "error"
    },
    {
        "id": "file_validation",
        "rule": "All referenced files must exist in the workspace",
        "severity": "error"
    }
]

Example frontmatter:
```yaml
---
description: Guidelines for implementing feature X
globs: ["**/*.py", "tests/**/*.py"]
related_docs: ["docs/architecture/feature-x.md"]
---
```

### 2. Metadata Annotations

@annotations {
    "syntax": "@annotation_name JSON_content",
    "placement": "Before relevant sections",
    "format": "Valid JSON with proper indentation",
    "types": {
        "context": "Project and document context",
        "rules": "List of rules or requirements",
        "format": "Format specifications",
        "options": "Available options",
        "examples": "Implementation examples",
        "implementations": "Full implementation details",
        "related": "Related documentation or code"
    }
}

### 3. Content Structure

@content_rules {
    "headings": {
        "h1": "Single main title",
        "h2": "Major sections",
        "h3": "Subsections",
        "h4": "Detailed points"
    },
    "code_blocks": {
        "syntax": "Always specify language",
        "examples": "Include practical examples",
        "formatting": "Use proper indentation",
        "context": "Add explanatory comments"
    },
    "implementation_blocks": {
        "structure": "Group related implementations",
        "documentation": "Include inline documentation",
        "types": "Specify type information",
        "validation": "Include validation rules"
    }
}

## Best Practices

@best_practices {
    "organization": {
        "sections": "Use clear hierarchical structure",
        "annotations": "Place before relevant content",
        "examples": "Include practical examples"
    },
    "formatting": {
        "json": "Properly formatted, valid JSON",
        "markdown": "Clean, consistent spacing",
        "code": "Language-specific syntax highlighting"
    },
    "metadata": {
        "annotations": "Use semantic names",
        "context": "Provide clear scope",
        "versioning": "Include version information"
    },
    "implementation": {
        "examples": "Provide complete, working examples",
        "types": "Include type definitions",
        "validation": "Specify validation rules",
        "error_handling": "Document error cases"
    }
}

## Implementation Guidelines

@implementation_rules {
    "code_examples": {
        "completeness": "Must be fully functional",
        "types": "Include all necessary type annotations",
        "imports": "Show all required imports including typing imports",
        "context": "Provide setup and usage context",
        "docstrings": "Include Google-style docstrings",
        "async": "Use proper async/await patterns when applicable",
        "error_handling": "Include proper exception handling"
    },
    "documentation": {
        "inline": "Add explanatory comments",
        "types": "Document type hints and constraints",
        "errors": "Document exceptions and error conditions",
        "usage": "Show usage patterns",
        "docstrings": {
            "style": "Google",
            "sections": [
                "Args",
                "Returns",
                "Raises",
                "Examples"
            ]
        }
    }
}

## Example Structure

### Basic Example
```markdown
---
description: Example implementation of feature X
globs: ["src/contextforge_cli/**/*.py", "tests/**/*.py"]
---

# Feature X Implementation

@context {
    "type": "implementation",
    "feature": "X",
    "version": "1.0.0",
    "python_version": ">=3.8"
}

## Overview
[Feature description]

## Implementation

@implementation {
    "language": "python",
    "dependencies": ["langchain>=0.3.17", "structlog>=24.4.0"],
    "types": {
        "CustomType": "Description of CustomType",
        "AsyncGenerator": "Async generator type for streaming responses"
    }
}

```python
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional, AsyncGenerator

import structlog

logger = structlog.get_logger()

class FeatureX:
    """Implementation of Feature X.

    This class demonstrates proper Python implementation patterns
    including typing, docstrings, and error handling.

    Attributes:
        name: The name of the feature
        config: Configuration dictionary
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize Feature X.

        Args:
            name: Feature name
            config: Optional configuration dictionary

        Raises:
            ValueError: If name is empty
        """
        if not name:
            raise ValueError("Name cannot be empty")
        self.name = name
        self.config = config or {}

    async def process(self) -> AsyncGenerator[str, None]:
        """Process data asynchronously.

        Yields:
            Processed data chunks

        Raises:
            ProcessingError: If processing fails
        """
        try:
            for i in range(10):
                yield f"Processing chunk {i}"
                await asyncio.sleep(0.1)
        except Exception as e:
            logger.exception("Processing failed", error=str(e))
            raise ProcessingError("Failed to process data") from e
```

## Usage Examples
[Usage examples with code]
```

### Common Patterns

@patterns {
    "rules_section": {
        "format": "array of objects",
        "properties": ["id", "severity", "description"],
        "example": [
            {
                "id": "rule_name",
                "severity": "error",
                "description": "Clear description"
            }
        ]
    },
    "implementation_section": {
        "format": "object with implementation details",
        "required": [
            "language",
            "types",
            "validation",
            "docstrings"
        ],
        "example": {
            "language": "python",
            "types": {
                "CustomType": "Description of type",
                "AsyncGenerator": "Async generator type"
            },
            "validation": {
                "type_checking": "Use mypy for static type checking",
                "runtime_validation": "Use Pydantic for runtime validation"
            },
            "docstrings": {
                "style": "Google",
                "required_sections": ["Args", "Returns", "Raises"]
            }
        }
    }
}

@python_standards {
    "typing": {
        "annotations": {
            "required": true,
            "style": "PEP 484",
            "features": [
                "Type hints for all functions and methods",
                "Return type annotations",
                "Generic types with TypeVar",
                "Proper async types (AsyncGenerator, Awaitable)",
                "Optional and Union types",
                "Literal types for constants",
                "TypedDict for structured dictionaries",
                "Protocol for structural subtyping"
            ]
        },
        "imports": {
            "from_typing": [
                "Any", "Dict", "List", "Optional", "Union",
                "AsyncGenerator", "Awaitable", "Callable",
                "TypeVar", "Generic", "Protocol", "runtime_checkable"
            ],
            "from_typing_extensions": [
                "Annotated", "TypedDict", "NotRequired",
                "Required", "Final", "Literal"
            ]
        }
    },
    "docstrings": {
        "style": "Google",
        "required_sections": [
            "Args",
            "Returns",
            "Raises",
            "Examples (when appropriate)"
        ],
        "format": {
            "standard": "PEP 257",
            "indentation": "4 spaces",
            "sections": {
                "Args": {
                    "format": "param_name (type): description",
                    "required": true
                },
                "Returns": {
                    "format": "type: description",
                    "required": true
                },
                "Raises": {
                    "format": "ExceptionType: description",
                    "required": true
                },
                "Examples": {
                    "format": "Code block with doctest format",
                    "required": false
                }
            }
        }
    },
    "error_handling": {
        "exceptions": {
            "hierarchy": "Define custom exception hierarchy",
            "base_class": "Create domain-specific base exception",
            "naming": "Suffix with Error (e.g., ProcessingError)",
            "context": "Include error context in exception message"
        },
        "logging": {
            "library": "structlog",
            "practices": [
                "Use bound loggers",
                "Include context in log messages",
                "Proper error level selection",
                "Exception traceback capture"
            ]
        }
    },
    "async_patterns": {
        "io_operations": {
            "files": "Use aiofiles for file operations",
            "network": "Use aiohttp for HTTP requests",
            "database": "Use asyncpg for PostgreSQL"
        },
        "concurrency": {
            "patterns": [
                "asyncio.gather for parallel operations",
                "asyncio.create_task for background tasks",
                "asyncio.Queue for producer-consumer patterns"
            ],
            "context_managers": [
                "async with for resource management",
                "asynccontextmanager for custom contexts"
            ]
        }
    },
    "testing": {
        "framework": {
            "primary": "pytest",
            "plugins": [
                "pytest-asyncio",
                "pytest-mock",
                "pytest-cov",
                "pytest-xdist"
            ]
        },
        "practices": {
            "fixtures": {
                "scope": ["function", "class", "module", "session"],
                "async_support": "Use @pytest.mark.asyncio",
                "cleanup": "Use yield fixtures for cleanup"
            },
            "mocking": {
                "tool": "pytest-mock",
                "patterns": [
                    "Use mocker.patch for dependencies",
                    "Mock async functions with AsyncMock"
                ]
            },
            "assertions": {
                "style": "pytest assert statements",
                "async": "await async calls in tests",
                "exceptions": "Use pytest.raises"
            }
        }
    },
    "code_style": {
        "formatters": {
            "black": "Code formatting",
            "isort": "Import sorting",
            "ruff": "Linting and additional formatting"
        },
        "line_length": 88,
        "quotes": "double",
        "imports": {
            "order": [
                "future",
                "standard library",
                "third party",
                "first party",
                "local"
            ],
            "style": "Use absolute imports"
        }
    }
}

## Common Mistakes to Avoid

@mistakes [
    {
        "id": "missing_type_annotations",
        "wrong": "def process_data(data):",
        "correct": "def process_data(data: Dict[str, Any]) -> ProcessingResult:",
        "reason": "Type annotations are required for all functions and methods"
    },
    {
        "id": "incorrect_async_patterns",
        "wrong": "def read_file(path): return open(path).read()",
        "correct": "async def read_file(path: str) -> str: async with aiofiles.open(path) as f: return await f.read()",
        "reason": "Use async IO operations to prevent blocking"
    },
    {
        "id": "improper_exception_handling",
        "wrong": "except Exception as e: print(f'Error: {e}')",
        "correct": "except Exception as e: logger.exception('Operation failed', error=str(e))",
        "reason": "Use proper structured logging with context"
    },
    {
        "id": "missing_docstrings",
        "wrong": "class DataProcessor: ...",
        "correct": """class DataProcessor:
    \"\"\"Process data with proper documentation.

    Attributes:
        name: Processor name
    \"\"\"
    ...""",
        "reason": "All classes and functions must have Google-style docstrings"
    },
    {
        "id": "incorrect_imports",
        "wrong": "from typing import *",
        "correct": "from typing import Dict, List, Optional, Any",
        "reason": "Explicit imports are required, no wildcard imports"
    }
]

## Validation

@validation {
    "required": [
        "All functions and methods must have type annotations",
        "All classes and functions must have Google-style docstrings",
        "Proper async/await patterns for IO operations",
        "Structured logging with context",
        "Custom exception hierarchy",
        "Proper error handling and recovery",
        "Configuration using Pydantic models",
        "Test coverage with pytest"
    ],
    "recommended": [
        "Use TypeVar and Generic for generic types",
        "Implement Protocol for interface definitions",
        "Use dataclasses or Pydantic models for data structures",
        "Add runtime type checking where necessary",
        "Implement proper cleanup in async context managers",
        "Use dependency injection for better testing",
        "Add performance monitoring and metrics",
        "Implement proper retry mechanisms"
    ],
    "tools": {
        "linting": {
            "ruff": "Primary linter with all rules enabled",
            "mypy": "Static type checking with strict mode"
        },
        "formatting": {
            "black": "Code formatting",
            "isort": "Import sorting"
        },
        "testing": {
            "pytest": "Test framework with plugins",
            "coverage": "Code coverage reporting"
        }
    }
}

@version "1.2.0"
@last_updated "2025-02-09"

## Implementation Examples

@implementation {
    "language": "python",
    "dependencies": [
        "langchain>=0.3.17",
        "structlog>=24.4.0",
        "pydantic>=2.5.0",
        "aiofiles>=23.2.1"
    ],
    "types": {
        "ProcessingResult": "TypedDict for processing results",
        "AsyncGenerator": "Async generator for streaming responses",
        "ProcessingError": "Custom exception for processing failures"
    }
}

```python
from __future__ import annotations

import asyncio
from typing import (
    Any,
    Dict,
    List,
    Optional,
    AsyncGenerator,
    TypedDict,
    Protocol,
    runtime_checkable
)

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger()

class ProcessingError(Exception):
    """Base exception for processing errors.

    Attributes:
        message: Error message
        context: Additional error context
    """
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.context = context or {}

class ProcessingResult(TypedDict):
    """Result of a processing operation.

    Keys:
        success: Whether processing was successful
        data: Processed data
        errors: Optional list of errors
    """
    success: bool
    data: Dict[str, Any]
    errors: Optional[List[str]]

@runtime_checkable
class Processor(Protocol):
    """Protocol for objects that can process data."""

    async def process(self, data: Dict[str, Any]) -> ProcessingResult:
        """Process the given data.

        Args:
            data: Data to process

        Returns:
            ProcessingResult containing success status and processed data

        Raises:
            ProcessingError: If processing fails
        """
        ...

class Config(BaseModel):
    """Configuration for processing.

    Attributes:
        name: Process name
        max_retries: Maximum number of retry attempts
        timeout: Operation timeout in seconds
    """
    name: str = Field(..., description="Process name")
    max_retries: int = Field(default=3, ge=0, description="Maximum retry attempts")
    timeout: float = Field(default=30.0, gt=0, description="Operation timeout")

class FeatureProcessor:
    """Implementation of feature processing with proper Python patterns.

    This class demonstrates:
    - Type annotations
    - Async/await patterns
    - Error handling
    - Logging with context
    - Protocol implementation
    - Configuration management

    Attributes:
        name: Processor name
        config: Configuration object
    """

    def __init__(self, name: str, config: Optional[Config] = None) -> None:
        """Initialize the processor.

        Args:
            name: Processor name
            config: Optional configuration object

        Raises:
            ValueError: If name is empty
        """
        if not name:
            raise ValueError("Name cannot be empty")
        self.name = name
        self.config = config or Config(name=name)
        self.logger = logger.bind(processor_name=name)

    async def process_stream(self) -> AsyncGenerator[str, None]:
        """Process data asynchronously with streaming.

        Yields:
            Processed data chunks

        Raises:
            ProcessingError: If processing fails
        """
        try:
            async with asyncio.timeout(self.config.timeout):
                for i in range(10):
                    self.logger.info(
                        "Processing chunk",
                        chunk_number=i,
                        total_chunks=10
                    )
                    yield f"Processing chunk {i}"
                    await asyncio.sleep(0.1)
        except asyncio.TimeoutError as e:
            self.logger.error(
                "Processing timed out",
                timeout=self.config.timeout
            )
            raise ProcessingError(
                "Operation timed out",
                context={"timeout": self.config.timeout}
            ) from e
        except Exception as e:
            self.logger.exception(
                "Processing failed",
                error=str(e)
            )
            raise ProcessingError(
                "Failed to process data",
                context={"error": str(e)}
            ) from e

async def main() -> None:
    """Example usage of FeatureProcessor."""
    processor = FeatureProcessor(
        "example",
        Config(name="example", max_retries=3, timeout=5.0)
    )

    try:
        async for chunk in processor.process_stream():
            print(chunk)
    except ProcessingError as e:
        logger.error(
            "Processing error",
            error=str(e),
            context=e.context
        )

if __name__ == "__main__":
    asyncio.run(main())

```

## Dependency Management

@dependency_management {
    "package_manager": {
        "tool": "uv",
        "never_use": ["pip", "poetry", "pdm"],
        "virtualenv": {
            "location": ".venv",
            "creation": "Automatically created by UV at project root"
        },
        "commands": {
            "install": "uv pip install",
            "sync": "uv sync",
            "add": "uv pip install package_name",
            "remove": "uv pip uninstall package_name",
            "update": "uv pip install --upgrade package_name",
            "list": "uv pip list",
            "freeze": "uv pip freeze"
        },
        "best_practices": [
            "Always use uv sync for dependency installation",
            "Keep uv.lock in version control",
            "Never modify .venv directory manually",
            "Use pyproject.toml for package configuration",
            "Maintain explicit version pins in requirements"
        ]
    },
    "environment": {
        "virtual_environment": {
            "type": "venv",
            "location": ".venv/",
            "creation": "Automatic via UV",
            "activation": "Not needed with UV commands"
        },
        "python_version": ">=3.8"
    },
    "dependency_files": {
        "primary": {
            "file": "pyproject.toml",
            "purpose": "Project metadata and dependencies",
            "format": "TOML",
            "sections": [
                "project",
                "dependencies",
                "dev-dependencies",
                "build-system"
            ]
        },
        "lock": {
            "file": "uv.lock",
            "purpose": "Locked dependencies with exact versions",
            "management": "Automatically managed by UV",
            "version_control": "Must be committed to repository"
        }
    }
}

@dependency_example {
    "pyproject_example": {
        "file": "pyproject.toml",
        "content": """
[project]
name = "contextforge-cli"
version = "0.1.0"
description = "A powerful CLI tool for managing and enhancing AI context"
requires-python = ">=3.8"
dependencies = [
    "langchain>=0.3.17",
    "structlog>=24.4.0",
    "pydantic>=2.5.0",
    "aiofiles>=23.2.1"
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.1",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.9",
    "mypy>=1.8.0"
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
"""
    },
    "commands": {
        "setup": [
            "# Initial setup",
            "uv sync",
            "# Install with dev dependencies",
            "uv pip install -e '.[dev]'",
            "# Update dependencies",
            "uv sync"
        ],
        "daily_usage": [
            "# Add new package",
            "uv pip install new-package",
            "# Sync dependencies",
            "uv sync",
            "# Run tests",
            "uv run pytest"
        ]
    }
}

@dependency_validation {
    "requirements": [
        "Use UV exclusively for package management",
        "Maintain pyproject.toml with explicit versions",
        "Keep uv.lock in version control",
        "Use .venv for virtual environment",
        "Never modify virtual environment manually"
    ],
    "checks": [
        "Verify UV installation",
        "Check pyproject.toml format",
        "Validate dependency specifications",
        "Ensure uv.lock is present",
        "Verify .venv location"
    ],
    "tools": {
        "primary": "UV",
        "configuration": "pyproject.toml",
        "lock": "uv.lock",
        "environment": ".venv"
    }
}

## XML Tag Guidelines for Anthropic Models

@anthropic_xml_guidelines {
    "purpose": "Enhance MDC files with XML tags for better Anthropic model comprehension",
    "tag_types": {
        "context": {
            "tag": "<context>",
            "usage": "Provide context about the code or feature",
            "example": "<context>This feature handles async data processing</context>"
        },
        "implementation": {
            "tag": "<implementation>",
            "usage": "Describe implementation details",
            "example": "<implementation>Uses asyncio for concurrent operations</implementation>"
        },
        "requirements": {
            "tag": "<requirements>",
            "usage": "List technical requirements",
            "example": "<requirements>Requires Python 3.8+ and aiohttp</requirements>"
        },
        "constraints": {
            "tag": "<constraints>",
            "usage": "Define implementation constraints",
            "example": "<constraints>Must maintain memory usage below 100MB</constraints>"
        },
        "examples": {
            "tag": "<examples>",
            "usage": "Provide usage examples",
            "example": "<examples>Example code demonstrating the feature</examples>"
        }
    },
    "best_practices": [
        "Use XML tags for critical information that models should focus on",
        "Keep tags focused and concise",
        "Use consistent tag naming",
        "Nest tags logically when needed",
        "Include type hints within implementation tags"
    ],
    "tag_structure": {
        "nesting": "Allowed for logical grouping",
        "attributes": "Use when additional metadata is needed",
        "formatting": "Maintain clean indentation for nested tags"
    }
}

@xml_examples {
    "basic_usage": """
<feature name="async_processor">
    <context>
        Handles asynchronous data processing with proper error handling and logging
    </context>
    <implementation>
        <requirements>
            Python 3.8+
            aiohttp
            structlog
        </requirements>
        <code_block language="python">
            async def process_data(data: Dict[str, Any]) -> ProcessingResult:
                try:
                    result = await process_chunk(data)
                    return ProcessingResult(success=True, data=result)
                except Exception as e:
                    logger.error("Processing failed", error=str(e))
                    return ProcessingResult(success=False, error=str(e))
        </code_block>
    </implementation>
</feature>
    """,
    "complex_example": """
<module name="data_processor">
    <context>
        <description>Advanced data processing module with async capabilities</description>
        <purpose>Handle large-scale data processing with proper error handling</purpose>
    </context>
    <requirements>
        <dependencies>
            <dependency name="aiohttp" version=">=3.8.0"/>
            <dependency name="structlog" version=">=24.1.0"/>
        </dependencies>
        <python_version>>=3.8</python_version>
    </requirements>
    <implementation>
        <classes>
            <class name="DataProcessor">
                <description>Main processor class with async capabilities</description>
                <methods>
                    <method name="process_chunk">
                        <signature>async def process_chunk(self, data: Dict[str, Any]) -> ProcessingResult</signature>
                        <description>Process a single chunk of data asynchronously</description>
                    </method>
                </methods>
            </class>
        </classes>
    </implementation>
</module>
    """
}

@xml_validation {
    "requirements": [
        "All major features must include XML tags for context",
        "Implementation details must be wrapped in appropriate tags",
        "Code examples must include language specification",
        "Requirements must be clearly tagged",
        "Type hints must be included in implementation tags"
    ],
    "tag_rules": {
        "nesting": "Maximum 3 levels deep",
        "naming": "Use descriptive, lowercase names",
        "attributes": "Use for metadata and specifications",
        "content": "Keep content clear and focused"
    }
}

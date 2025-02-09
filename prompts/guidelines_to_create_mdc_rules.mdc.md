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
    "python_version": ">=3.8"
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
        "testing_guidelines"
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
        "annotations": "Required for all functions and classes",
        "imports": "Use typing module for complex types",
        "generics": "Use TypeVar and Generic for generic types",
        "async": "Use proper async types (AsyncGenerator, etc.)"
    },
    "docstrings": {
        "style": "Google",
        "required_sections": [
            "Args",
            "Returns",
            "Raises",
            "Examples (when appropriate)"
        ],
        "format": "Follow PEP 257"
    },
    "error_handling": {
        "exceptions": "Define custom exception hierarchy",
        "logging": "Use structlog for all logging",
        "context": "Include error context in exceptions"
    },
    "async_patterns": {
        "io": "Use aiofiles for file operations",
        "networking": "Use aiohttp for HTTP requests",
        "concurrency": "Use asyncio.gather for parallel operations"
    },
    "testing": {
        "framework": "pytest",
        "fixtures": "Define reusable fixtures",
        "async": "Use pytest-asyncio for async tests",
        "mocking": "Use pytest-mock for mocking"
    }
}

## Common Mistakes to Avoid

@mistakes [
    {
        "id": "missing_frontmatter",
        "wrong": "Starting directly with content",
        "correct": "Include frontmatter at top",
        "reason": "Frontmatter is required for Cursor to properly parse the file"
    },
    {
        "id": "invalid_json",
        "wrong": "Malformed JSON in annotations",
        "correct": "Properly formatted JSON with quotes around keys",
        "reason": "Annotations must contain valid JSON for proper parsing"
    },
    {
        "id": "inconsistent_structure",
        "wrong": "Mixed levels of headings",
        "correct": "Clear hierarchical structure",
        "reason": "Consistent structure helps with readability and parsing"
    },
    {
        "id": "nonexistent_files",
        "wrong": "Referencing files that don't exist in the workspace",
        "correct": "Only reference files that exist and have been verified",
        "reason": "Prevents broken links and maintains documentation integrity"
    }
]

## Validation

@validation {
    "required": [
        "Frontmatter must be present and valid",
        "All JSON must be properly formatted",
        "Main title must be present",
        "At least one content section",
        "Complete implementation examples when relevant",
        "All referenced files must exist in the workspace"
    ],
    "recommended": [
        "Version information",
        "Last updated date",
        "Clear examples",
        "Proper code formatting",
        "Type definitions",
        "Validation rules",
        "Verify file existence before referencing"
    ]
}

@version "1.2.0"
@last_updated "2024-03-19"

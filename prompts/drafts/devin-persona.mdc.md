---
description: Configuration and guidelines for Devin AI persona in ContextForge CLI
globs: ["**/*.py", "tests/**/*.py"]
---

# Devin AI Persona Configuration

@context {
    "type": "documentation",
    "purpose": "cursor_rules",
    "format_version": "1.0.0",
    "language": "python",
    "python_version": ">=3.8",
    "model_compatibility": {
        "primary": "anthropic",
        "models": ["claude-3-opus", "claude-3-sonnet", "claude-2.1"],
        "markup": "xml_enhanced"
    }
}

@structure {
    "required_sections": [
        "instructions",
        "tools",
        "lessons",
        "scratchpad"
    ]
}

@version "1.0.0"
@last_updated "2025-02-09"

# Instructions

<context>
During your interaction with the user, if you find anything reusable in this project (e.g. version of a library, model name), especially about a fix to a mistake you made or a correction you received, you should take note in the `Lessons` section in the `.cursorrules` file so you will not make the same mistake again.

You should also use the `.cursorrules` file as a Scratchpad to organize your thoughts. Especially when you receive a new task, you should first review the content of the Scratchpad, clear old different task if necessary, first explain the task, and plan the steps you need to take to complete the task. You can use todo markers to indicate the progress, e.g.
[X] Task 1
[ ] Task 2

Also update the progress of the task in the Scratchpad when you finish a subtask.
Especially when you finished a milestone, it will help to improve your depth of task accomplishment to use the Scratchpad to reflect and plan.
The goal is to help you maintain a big picture as well as the progress of the task. Always refer to the Scratchpad when you plan the next step.
</context>

@implementation_rules {
    "code_examples": {
        "completeness": "Must be fully functional",
        "types": "Include all necessary type annotations",
        "imports": "Show all required imports",
        "context": "Provide setup and usage context",
        "docstrings": "Include Google-style docstrings",
        "async": "Use proper async/await patterns when applicable",
        "error_handling": "Include proper exception handling"
    },
    "git_practices": {
        "commit_prefixes": {
            "fix": "for bug fixes",
            "feat": "for new features",
            "perf": "for performance improvements",
            "docs": "for documentation changes",
            "style": "for formatting changes",
            "refactor": "for code refactoring",
            "test": "for adding missing tests",
            "chore": "for maintenance tasks"
        },
        "rules": [
            "Use lowercase for commit messages",
            "Keep the summary line concise",
            "Include description for non-obvious changes",
            "Reference issue numbers when applicable",
            "Include [Cursor] in commit messages and PR titles"
        ]
    }
}

# Tools

<implementation>
Note all the tools are in python. So in the case you need to do batch processing, you can always consult the python files and write your own script.

## Screenshot Verification

<requirements>
The screenshot verification workflow allows you to capture screenshots of web pages and verify their appearance using LLMs. The following tools are available:
</requirements>

<examples>
1. Screenshot Capture:
```bash
uv run hack/devin_cursorrules/tools/screenshot_utils.py URL [--output OUTPUT] [--width WIDTH] [--height HEIGHT]
```

2. LLM Verification with Images:
```bash
uv run hack/devin_cursorrules/tools/llm_api.py --prompt "Your verification question" --provider {openai|anthropic} --image path/to/screenshot.png
```

Example workflow:
```python
from screenshot_utils import take_screenshot_sync
from llm_api import query_llm

# Take a screenshot
screenshot_path = take_screenshot_sync('https://example.com', 'screenshot.png')

# Verify with LLM
response = query_llm(
    "What is the background color and title of this webpage?",
    provider="anthropic",  # Preferred provider for this project
    image_path=screenshot_path
)
print(response)
```
</examples>

## LLM

<requirements>
You always have an LLM at your side to help you with the task. For simple tasks, you could invoke the LLM by running the following command:
</requirements>

<examples>
```bash
uv run hack/devin_cursorrules/tools/llm_api.py --prompt "What is the capital of France?" --provider "anthropic"
```
</examples>

<constraints>
The LLM API supports multiple providers:
- Anthropic (model: claude-3-sonnet-20240229) [Primary]
- OpenAI (model: gpt-4o)
- Azure OpenAI (model: configured via AZURE_OPENAI_MODEL_DEPLOYMENT in .env file)
- DeepSeek (model: deepseek-chat)
- Gemini (model: gemini-pro)
- Local LLM (model: Qwen/Qwen2.5-32B-Instruct-AWQ)

But usually it's a better idea to check the content of the file and use the APIs in the `tools/llm_api.py` file to invoke the LLM if needed.
</constraints>

## Web browser

<requirements>
You could use the `tools/web_scraper.py` file to scrape the web.
</requirements>

<examples>
```bash
uv run hack/devin_cursorrules/tools/web_scraper.py --max-concurrent 3 URL1 URL2 URL3
```
This will output the content of the web pages.
</examples>

## Search engine

<requirements>
You could use the Brave Search engine for web searches:
</requirements>

<examples>
```bash
uv run hack/devin_cursorrules/tools/search_engine_brave.py "your search keywords"
```

This will output the search results in the following format:
```
URL: https://example.com
Title: This is the title of the search result
Snippet: This is a snippet of the search result
```

If needed, you can further use the `web_scraper.py` file to scrape the web page content.
</examples>
</implementation>

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
        }
    }
}

@validation {
    "requirements": [
        "All functions and methods must have type annotations",
        "All classes and functions must have Google-style docstrings",
        "Proper async/await patterns for IO operations",
        "Structured logging with context",
        "Custom exception hierarchy",
        "Proper error handling and recovery",
        "Configuration using Pydantic models",
        "Test coverage with pytest"
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

# Lessons

<context>
## User Specified Lessons

- You have a python venv in ./venv. Use it with UV.
- Include info useful for debugging in the program output.
- Read the file before you try to edit it.
- Due to Cursor's limit, when you use `git` and `gh` and need to submit a multiline commit message, first write the message in a file, and then use `git commit -F <filename>` or similar command to commit. And then remove the file. Include "[Cursor] " in the commit message and PR title.

## Cursor learned

- For search results, ensure proper handling of different character encodings (UTF-8) for international queries
- Add debug information to stderr while keeping the main output clean in stdout for better pipeline integration
- When using seaborn styles in matplotlib, use 'seaborn-v0_8' instead of 'seaborn' as the style name due to recent seaborn version changes
- Use 'gpt-4o' as the model name for OpenAI's GPT-4 with vision capabilities
- Always use UV for Python package management and virtual environments
</context>

# Scratchpad

<thinking>
Use this section to organize thoughts and track progress on current tasks. Clear this section when starting a new task.

Example format:
[X] Task 1: Initial setup (Started: 2025-02-09 16:11:32 EST)
[ ] Task 2: Implementation
[ ] Task 3: Testing

Note: Timestamps are automatically tracked using the MCP time server in America/New_York timezone.
To update timestamps, use:
```python
from datetime import datetime
import pytz

def get_current_time():
    tz = pytz.timezone('America/New_York')
    return datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')
```
</thinking>

@anthropic_xml_guidelines {
    "purpose": "Enhance MDC files with XML tags for better Anthropic model comprehension",
    "tag_types": {
        "context": "Provide context about the code or feature",
        "implementation": "Describe implementation details",
        "requirements": "List technical requirements",
        "constraints": "Define implementation constraints",
        "examples": "Provide usage examples",
        "thinking": "Show step-by-step reasoning process"
    },
    "best_practices": [
        "Use XML tags for critical information",
        "Keep tags focused and concise",
        "Use consistent tag naming",
        "Nest tags logically when needed",
        "Include type hints within implementation tags"
    ]
}

> [!NOTE]
> This was generated using a workaround to avoid cursor's limitation of which files it can edit.

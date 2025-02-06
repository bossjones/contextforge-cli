import json
import os
from typing import Any, Dict, Optional


def load_config() -> dict[str, Any] | None:
    """Load configuration settings from config.json file.

    Attempts to load configuration from a config.json file in the same directory as this script.
    If the file doesn't exist or there's an error loading it, returns the default configuration.

    Returns:
        Optional[Dict[str, Any]]: The loaded configuration dictionary if successful,
            the default configuration if the file doesn't exist,
            or None if there was an error loading the configuration.

    Note:
        Only processes .json files and falls back to default config for other file types.
    """
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, "config.json")

        if os.path.exists(config_path):
            with open(config_path) as f:
                if config_path.endswith(".json"):
                    return json.load(f)

        return get_default_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        return None


def get_default_config() -> dict[str, Any]:
    """Get the default configuration settings.

    Returns:
        Dict[str, Any]: A dictionary containing default configuration settings:
            - project_path (str): Empty string by default
            - update_interval (int): Default update interval in seconds
            - max_depth (int): Maximum directory traversal depth
            - ignored_directories (List[str]): List of directory names to ignore
            - ignored_files (List[str]): List of file patterns to ignore
            - binary_extensions (List[str]): List of binary file extensions
            - file_length_standards (Dict[str, int]): Maximum line lengths by file extension
    """
    return {
        "project_path": "",
        "update_interval": 60,
        "max_depth": 3,
        "ignored_directories": [
            "__pycache__",
            "node_modules",
            "venv",
            ".git",
            ".idea",
            ".vscode",
            "dist",
            "build",
            "coverage",
        ],
        "ignored_files": [
            ".DS_Store",
            "Thumbs.db",
            "*.pyc",
            "*.pyo",
            "package-lock.json",
            "yarn.lock",
        ],
        "binary_extensions": [
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".ico",
            ".pdf",
            ".exe",
            ".bin",
        ],
        "file_length_standards": {
            ".py": 400,  # Python
            ".js": 300,  # JavaScript
            ".ts": 300,  # TypeScript
            ".tsx": 300,  # TypeScript/React
            ".kt": 300,  # Kotlin
            ".php": 400,  # PHP
            ".swift": 400,  # Swift
            ".cpp": 500,  # C++
            ".c": 500,  # C
            ".h": 300,  # C/C++ Header
            ".hpp": 300,  # C++ Header
            ".cs": 400,  # C#
            ".csx": 400,  # C# Script
            "default": 300,
        },
    }


# Load configuration once at module level
_config: dict[str, Any] | None = load_config()

# Binary file extensions that should be ignored
BINARY_EXTENSIONS: set[str] = set(_config.get("binary_extensions", []))

# Documentation and text files that shouldn't be analyzed for functions
NON_CODE_EXTENSIONS: set[str] = {
    ".md",
    ".txt",
    ".log",
    ".json",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".config",
    ".markdown",
    ".rst",
    ".rdoc",
    ".csv",
    ".tsv",
}

# Extensions that should be analyzed for code
CODE_EXTENSIONS: set[str] = {
    ".py",  # Python
    ".js",  # JavaScript
    ".ts",  # TypeScript
    ".tsx",  # TypeScript/React
    ".kt",  # Kotlin
    ".php",  # PHP
    ".swift",  # Swift
    ".cpp",  # C++
    ".c",  # C
    ".h",  # C/C++ Header
    ".hpp",  # C++ Header
    ".cs",  # C#
    ".csx",  # C# Script
}

# Regex patterns for function detection
FUNCTION_PATTERNS: dict[str, str] = {
    # Python
    "python_function": r"def\s+([a-zA-Z_]\w*)\s*\(",
    "python_class": r"class\s+([a-zA-Z_]\w*)\s*[:\(]",
    # JavaScript/TypeScript
    "js_function": r"(?:^|\s+)(?:function\s+([a-zA-Z_]\w*)|(?:const|let|var)\s+([a-zA-Z_]\w*)\s*=\s*(?:async\s*)?function)",
    "js_arrow": r"(?:^|\s+)(?:const|let|var)\s+([a-zA-Z_]\w*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[^=])\s*=>",
    "js_method": r"\b([a-zA-Z_]\w*)\s*:\s*(?:async\s*)?function",
    "js_class_method": r"(?:^|\s+)(?:async\s+)?([a-zA-Z_]\w*)\s*\([^)]*\)\s*{",
    # PHP
    "php_function": r"(?:public\s+|private\s+|protected\s+)?function\s+([a-zA-Z_]\w*)\s*\(",
    # C/C++
    "cpp_function": r"(?:virtual\s+)?(?:static\s+)?(?:inline\s+)?(?:const\s+)?(?:\w+(?:::\w+)*\s+)?([a-zA-Z_]\w*)\s*\([^)]*\)(?:\s*const)?(?:\s*noexcept)?(?:\s*override)?(?:\s*final)?(?:\s*=\s*0)?(?:\s*=\s*default)?(?:\s*=\s*delete)?(?:{|;)",
    # C#
    "csharp_method": r"(?:public|private|protected|internal|static|virtual|override|abstract|sealed|async)\s+(?:\w+(?:<[^>]+>)?)\s+([a-zA-Z_]\w*)\s*\([^)]*\)",
    # Kotlin
    "kotlin_function": r"(?:fun\s+)?([a-zA-Z_]\w*)\s*(?:<[^>]+>)?\s*\([^)]*\)(?:\s*:\s*[^{]+)?\s*{",
    # Swift
    "swift_function": r"(?:func\s+)([a-zA-Z_]\w*)\s*(?:<[^>]+>)?\s*\([^)]*\)(?:\s*->\s*[^{]+)?\s*{",
}

# Keywords that should not be treated as function names
IGNORED_KEYWORDS: set[str] = {
    "if",
    "switch",
    "while",
    "for",
    "catch",
    "finally",
    "else",
    "return",
    "break",
    "continue",
    "case",
    "default",
    "to",
    "from",
    "import",
    "as",
    "try",
    "except",
    "raise",
    "with",
    "async",
    "await",
    "yield",
    "assert",
    "pass",
    "del",
    "print",
    "in",
    "is",
    "not",
    "and",
    "or",
    "lambda",
    "global",
    "nonlocal",
    "class",
    "def",
}

# Names of files and directories that should be ignored
IGNORED_NAMES: set[str] = set(_config.get("ignored_directories", []))

FILE_LENGTH_STANDARDS: dict[str, int] = _config.get("file_length_standards", {})


def get_file_length_limit(file_path: str) -> int:
    """Get the recommended maximum line limit for a given file type.

    Args:
        file_path: Path to the file to check.

    Returns:
        int: The recommended maximum number of lines for the file type.
            Returns the extension-specific limit if defined,
            otherwise returns the default limit (300 lines).
    """
    ext = os.path.splitext(file_path)[1].lower()
    return FILE_LENGTH_STANDARDS.get(ext, FILE_LENGTH_STANDARDS.get("default", 300))

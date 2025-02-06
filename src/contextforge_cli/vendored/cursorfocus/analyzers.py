import logging
import os
import re

from contextforge_cli.vendored.cursorfocus.config import (
    BINARY_EXTENSIONS,
    CODE_EXTENSIONS,
    FUNCTION_PATTERNS,
    IGNORED_KEYWORDS,
    IGNORED_NAMES,
    NON_CODE_EXTENSIONS,
)


def is_binary_file(filename):
    """Check if a file is binary or non-code based on its extension."""
    ext = os.path.splitext(filename)[1].lower()

    # Binary extensions
    if ext in BINARY_EXTENSIONS:
        return True

    # Documentation and text files that shouldn't be analyzed for functions
    return ext in NON_CODE_EXTENSIONS


def should_ignore_file(name):
    """Check if a file or directory should be ignored."""
    return name in IGNORED_NAMES or name.startswith(".")


def analyze_file_content(file_path):
    """Analyze file content for functions and their descriptions."""
    try:
        # Skip binary and non-code files
        if is_binary_file(file_path):
            return [], 0

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Skip files that don't look like actual code files
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in CODE_EXTENSIONS:
            return [], 0

        functions = []

        # Use patterns for function detection
        for pattern_name, pattern in FUNCTION_PATTERNS.items():
            try:
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                for match in matches:
                    func_name = next(filter(None, match.groups()), None)
                    if not func_name or func_name.lower() in IGNORED_KEYWORDS:
                        continue
                    functions.append((func_name, "Function detected"))
            except re.error as e:
                logging.debug(
                    f"Invalid regex pattern {pattern_name} for {file_path}: {e}"
                )
                continue
            except Exception as e:
                logging.debug(
                    f"Error analyzing pattern {pattern_name} for {file_path}: {e}"
                )
                continue

        return functions, len(content.split("\n"))
    except Exception as e:
        print(f"Error analyzing file {file_path}: {e}")
        return [], 0

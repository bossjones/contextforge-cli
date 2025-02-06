import logging
import os
import re
from typing import List, Tuple

from contextforge_cli.vendored.cursorfocus.config import (
    BINARY_EXTENSIONS,
    CODE_EXTENSIONS,
    FUNCTION_PATTERNS,
    IGNORED_KEYWORDS,
    IGNORED_NAMES,
    NON_CODE_EXTENSIONS,
)


def is_binary_file(filename: str) -> bool:
    """Check if a file is binary or non-code based on its extension.

    Args:
        filename: The name of the file to check.

    Returns:
        bool: True if the file is binary or non-code, False otherwise.
    """
    ext = os.path.splitext(filename)[1].lower()

    # Binary extensions
    if ext in BINARY_EXTENSIONS:
        return True

    # Documentation and text files that shouldn't be analyzed for functions
    return ext in NON_CODE_EXTENSIONS


def should_ignore_file(name: str) -> bool:
    """Check if a file or directory should be ignored during analysis.

    Args:
        name: The name of the file or directory to check.

    Returns:
        bool: True if the file/directory should be ignored, False otherwise.
    """
    return name in IGNORED_NAMES or name.startswith(".")


def analyze_file_content_and_desc(file_path: str) -> tuple[list[tuple[str, str]], int]:
    """Analyze file content for functions and their descriptions.

    This function reads a file and attempts to detect function definitions using regex patterns.
    It skips binary files and files with non-code extensions.

    Args:
        file_path: Path to the file to analyze.

    Returns:
        Tuple containing:
            - List[Tuple[str, str]]: List of tuples where each tuple contains:
                - Function name (str)
                - Function description (str)
            - int: Total number of lines in the file

    Note:
        Returns empty list and 0 lines if file is binary, non-code, or encounters an error.
    """
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

        functions: list[tuple[str, str]] = []

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

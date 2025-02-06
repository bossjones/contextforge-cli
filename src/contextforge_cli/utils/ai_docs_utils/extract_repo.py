from __future__ import annotations

import ast
import os
import shutil
import sys


def make_zip_file(directory_path: str, output_file_name: str) -> str:
    """Zip the given directory of a local repository.

    Args:
        directory_path: Path to the directory to zip
        output_file_name: Name of the output zip file without extension

    Returns:
        str: Path to the created zip file with extension
    """
    shutil.make_archive(output_file_name, "zip", directory_path)
    return f"{output_file_name}.zip"


def is_desired_file(file_path: str) -> bool:
    """Check if the file is a relevant coding file or a key project file.

    Args:
        file_path: Path to the file to check

    Returns:
        bool: True if file is a desired type, False otherwise
    """
    # Convert to lowercase for case-insensitive comparison
    file_path_lower = file_path.lower()

    # Check for specific file types (case-insensitive)
    if file_path_lower.endswith((".ts", ".tsx", ".prisma", ".py")):
        return True

    # Check for specific file names (case-insensitive)
    if os.path.basename(file_path_lower) in ("package.json", "pyproject.toml"):
        return True

    return False


def is_likely_useful_file(file_path: str) -> bool:
    """Determine if the file is likely to be useful by excluding certain directories and specific file types.

    Args:
        file_path: Path to the file to check

    Returns:
        bool: True if file is likely useful, False otherwise
    """
    excluded_dirs = [
        "docs",
        "examples",
        "tests",
        "test",
        "__pycache__",
        "scripts",
        "benchmarks",
        "node_modules",
        ".venv",
    ]
    utility_or_config_files = ["hubconf.py", "setup.py", "package-lock.json"]
    github_workflow_or_docs = ["stale.py", "gen-card-", "write_model_card"]

    # Normalize path separators
    check_path = file_path.replace("\\", "/")

    # Split path into components
    parts = check_path.split("/")

    # Check for hidden files/directories (starting with .)
    if any(part.startswith(".") for part in parts):
        return False

    # Check for test-related paths more precisely
    check_path_lower = check_path.lower()
    if any(
        part.startswith("test") or part.endswith("test")
        for part in check_path_lower.split("/")
    ):
        return False

    # Check excluded directories
    for excluded_dir in excluded_dirs:
        if f"/{excluded_dir}/" in check_path or check_path.startswith(
            f"{excluded_dir}/"
        ):
            return False

    # Check utility/config files
    for file_name in utility_or_config_files:
        if file_name in check_path:
            return False

    # Check GitHub workflow files
    if not all(doc_file not in check_path for doc_file in github_workflow_or_docs):
        return False

    return True


def has_sufficient_content(file_content: list[str], min_line_count: int = 5) -> bool:
    """Check if the file has a minimum number of substantive lines.

    Args:
        file_content: List of lines from the file
        min_line_count: Minimum number of substantive lines required (default: 5)

    Returns:
        bool: True if file has sufficient content, False otherwise
    """
    lines = [
        line
        for line in file_content
        if line.strip() and not line.strip().startswith("//")
    ]
    return len(lines) >= min_line_count


def remove_comments_and_docstrings(source: str) -> str:
    """Remove comments and docstrings from the Python source code.

    Args:
        source: Python source code as string

    Returns:
        str: Source code with comments and docstrings removed
    """
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)
        ) and ast.get_docstring(node):
            node.body = node.body[1:]  # Remove docstring
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Str):
            node.value.s = ""  # Remove comments
    return ast.unparse(tree)


def extract_local_directory(directory_path: str) -> str:
    """Walks through a local directory and converts relevant code files to a .txt file.

    Args:
        directory_path: Path to the local repository directory

    Returns:
        str: Name of the output file containing extracted code
    """
    # Get absolute paths
    abs_directory_path = os.path.abspath(directory_path)
    repo_name = os.path.basename(abs_directory_path)
    output_file = f"{repo_name}_code.txt"

    with open(output_file, "w", encoding="utf-8") as outfile:
        for root, _, files in os.walk(abs_directory_path):
            for file in files:
                abs_file_path = os.path.join(root, file)
                # Get path relative to the repository root
                rel_file_path = os.path.relpath(abs_file_path, abs_directory_path)

                # Skip directories, non-code files, less likely useful files, hidden directories, and test files
                if (
                    rel_file_path.endswith("/")
                    or not is_desired_file(rel_file_path)
                    or not is_likely_useful_file(rel_file_path)
                ):
                    continue

                try:
                    with open(abs_file_path, encoding="utf-8") as file_content:
                        file_lines = file_content.readlines()

                        # For code files, check content length. For config files, always include
                        is_config = rel_file_path.lower() in [
                            "package.json",
                            "pyproject.toml",
                        ]
                        if is_config or has_sufficient_content(file_lines):
                            outfile.write(f"# File: {rel_file_path}\n")
                            outfile.writelines(file_lines)
                            outfile.write("\n\n")
                except (OSError, UnicodeDecodeError) as e:
                    print(f"Error processing file {rel_file_path}: {e}")
                    continue

    return output_file


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_repo.py <local repository directory>")
        sys.exit(1)

    directory_path = sys.argv[1]
    extract_local_directory(directory_path)

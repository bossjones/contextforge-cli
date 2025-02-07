import json
import os
import re
import time
from collections.abc import Callable
from typing import Any, Dict, List, Optional, Set, Tuple, TypedDict, Union

from contextforge_cli.vendored.cursorfocus.config import load_config


class ProjectInfo(TypedDict):
    """Type definition for project information dictionary.

    Attributes:
        type: The detected project type
        language: Primary programming language
        framework: Detected framework or 'none'
        description: Human-readable project description
        matched_files: List of files that matched project type indicators
        path: Path to the project directory
    """

    type: str
    language: str
    framework: str
    description: str
    matched_files: list[str]
    path: str


class ProjectTypeInfo(TypedDict):
    """Type definition for project type configuration.

    Attributes:
        description: Human-readable description of the project type
        indicators: List of files/patterns that indicate this project type
        file_patterns: List of file patterns associated with this type
        required_files: List of files that must be present
        priority: Priority level for detection (higher = more specific)
        additional_checks: Optional list of callable checks
    """

    description: str
    indicators: list[str]
    file_patterns: list[str]
    required_files: list[str]
    priority: int
    additional_checks: list[Callable[[str], bool]] | None


# Load project types from config at module level
_config: dict[str, Any] | None = load_config()

# Project type definitions with improved structure
PROJECT_TYPES: dict[str, ProjectTypeInfo] = {
    "python": {
        "description": "Python Project",
        "indicators": [
            "setup.py",
            "requirements.txt",
            "Pipfile",
            "pyproject.toml",
            "poetry.lock",
            "venv/",
            ".venv/",
        ],
        "file_patterns": ["*.py"],
        "required_files": [],
        "priority": 10,
        "additional_checks": [
            lambda path: any(
                f.endswith(".py")
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            )
        ],
    },
    "java": {
        "description": "Java Project",
        "indicators": [
            "pom.xml",
            "build.gradle",
            "gradlew",
            ".gradle/",
            "src/main/java/",
            "target/",
            "META-INF/",
        ],
        "file_patterns": ["*.java", "*.jar", "*.war"],
        "required_files": [],
        "priority": 7,
        "additional_checks": [
            lambda path: any(
                f.endswith(".java")
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            )
        ],
    },
    "go": {
        "description": "Go Project",
        "indicators": ["go.mod", "go.sum", "main.go", "pkg/", "cmd/", "internal/"],
        "file_patterns": ["*.go"],
        "required_files": [],
        "priority": 7,
        "additional_checks": [
            lambda path: any(
                f.endswith(".go")
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            )
        ],
    },
    "ruby": {
        "description": "Ruby Project",
        "indicators": [
            "Gemfile",
            "Rakefile",
            ".ruby-version",
            "config.ru",
            "bin/rails",
            "app/",
            "lib/",
        ],
        "file_patterns": ["*.rb", "*.erb", "*.rake"],
        "required_files": [],
        "priority": 6,
        "additional_checks": [
            lambda path: any(
                f.endswith(".rb")
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            )
        ],
    },
    "rust": {
        "description": "Rust Project",
        "indicators": [
            "Cargo.toml",
            "Cargo.lock",
            "src/main.rs",
            "src/lib.rs",
            "target/",
        ],
        "file_patterns": ["*.rs"],
        "required_files": [],
        "priority": 7,
        "additional_checks": [
            lambda path: any(
                f.endswith(".rs")
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            )
        ],
    },
    "dart": {
        "description": "Dart/Flutter Project",
        "indicators": [
            "pubspec.yaml",
            "pubspec.lock",
            ".dart_tool/",
            "android/",
            "ios/",
            "lib/",
            "test/",
        ],
        "file_patterns": ["*.dart"],
        "required_files": [],
        "priority": 6,
        "additional_checks": [
            lambda path: any(
                f.endswith(".dart")
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            )
        ],
    },
    "scala": {
        "description": "Scala Project",
        "indicators": [
            "build.sbt",
            "project/build.properties",
            ".scala-build/",
            "src/main/scala/",
        ],
        "file_patterns": ["*.scala"],
        "required_files": [],
        "priority": 6,
        "additional_checks": [
            lambda path: any(
                f.endswith(".scala")
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            )
        ],
    },
    "javascript": {
        "description": "JavaScript/Node.js Project",
        "indicators": [
            "package.json",
            "package-lock.json",
            "yarn.lock",
            "node_modules/",
            "webpack.config.js",
            ".npmrc",
            ".nvmrc",
            "next.config.js",
        ],
        "file_patterns": ["*.js", "*.jsx", "*.mjs", "*.cjs"],
        "required_files": [],
        "priority": 5,
        "additonal_checks": [
            lambda path: any(
                f.endswith((".js", ".jsx", ".mjs", ".cjs"))
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            )
        ],
    },
    "typescript": {
        "description": "TypeScript Project",
        "indicators": [
            "tsconfig.json",
            "tslint.json",
            "typescript.json",
            ".ts",
            ".tsx",
            ".eslintrc",
        ],
        "file_patterns": ["*.ts", "*.tsx"],
        "required_files": [],
        "priority": 6,  # Higher than JS because TS projects often have JS files too
        "additional_checks": [
            lambda path: any(
                f.endswith((".ts", ".tsx"))
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            )
        ],
    },
    "web": {
        "description": "Web Project",
        "indicators": [
            "index.html",
            "styles.css",
            ".html",
            ".css",
            "public/",
            "assets/",
            "images/",
        ],
        "file_patterns": ["*.html", "*.css", "*.scss", "*.sass", "*.less", "*.svg"],
        "required_files": [],
        "priority": 3,
    },
    "php": {
        "description": "PHP Project",
        "indicators": ["composer.json", "composer.lock", "artisan", ".php", "vendor/"],
        "file_patterns": ["*.php"],
        "required_files": [],
        "priority": 5,
        "additional_checks": [
            lambda path: any(
                f.endswith(".php")
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            )
        ],
    },
    "cpp": {
        "description": "C++ Project",
        "indicators": [
            "CMakeLists.txt",
            "makefile",
            "Makefile",
            ".sln",
            ".vcxproj",
            "compile_commands.json",
        ],
        "file_patterns": ["*.cpp", "*.hpp", "*.cc", "*.h", "*.cxx", "*.hxx"],
        "required_files": [],
        "priority": 5,
        "additional_checks": [
            lambda path: any(
                f.endswith((".cpp", ".hpp", ".cc", ".cxx", ".h", ".hxx"))
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            )
        ],
    },
    "csharp": {
        "description": "C# Project",
        "indicators": [
            ".sln",
            ".csproj",
            ".cs",
            "packages.config",
            "NuGet.Config",
            "bin/Debug/",
            "bin/Release/",
        ],
        "file_patterns": ["*.cs"],
        "required_files": [],
        "priority": 5,
        "additional_checks": [
            lambda path: any(
                f.endswith(".cs")
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            )
        ],
    },
    "kotlin": {
        "description": "Kotlin Project",
        "indicators": ["*.kt", "build.gradle.kts", ".kt"],
        "file_patterns": ["*.kt", "*.kts"],
        "required_files": [],
        "priority": 5,
        "additional_checks": [
            lambda path: any(
                f.endswith((".kt", ".kts"))
                for f in os.listdir(path)
                if os.path.isfile(os.path.join(path, f))
            )
        ],
    },
}

# Add cache for scan results with expiration
_scan_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
CACHE_EXPIRATION: int = 300  # 5 minutes

IGNORED_DIRECTORIES: set[str] = {
    ".git",
    ".github",
    "__pycache__",
    "node_modules",
    "venv",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    ".idea",
    ".vscode",
}


def detect_project_type(project_path: str) -> ProjectInfo:
    """Detect the type of project in the given directory with improved accuracy.

    This function analyzes a directory to determine the type of project it contains,
    using various indicators like file patterns, required files, and additional checks.

    Args:
        project_path: Path to the project directory to analyze

    Returns:
        ProjectInfo: Dictionary containing project information:
            - type: Detected project type (e.g., 'python', 'javascript')
            - language: Primary programming language
            - framework: Detected framework or 'none'
            - description: Human-readable project description
            - matched_files: List of files that matched project type indicators
            - path: Path to the project directory

    Note:
        - Returns generic project info if path doesn't exist or is inaccessible
        - Uses a priority system to handle projects with multiple indicators
        - Performs additional checks specific to each project type
    """
    if not os.path.exists(project_path):
        return _get_generic_result()

    try:
        files = os.listdir(project_path)
        files_set = set(files)  # For faster lookups
    except (PermissionError, OSError):
        return _get_generic_result()

    # Get all files recursively up to depth 2 for better detection
    all_files = _get_files_recursive(project_path, max_depth=2)

    project_type = "generic"
    max_priority = -1
    matched_files: list[str] = []

    # Check each project type
    for type_name, rules in PROJECT_TYPES.items():
        priority = rules.get("priority", 0)
        matched = False
        type_matched_files: list[str] = []

        # Check direct indicators (files/folders that strongly indicate a project type)
        for indicator in rules.get("indicators", []):
            if _check_indicator(indicator, files_set, all_files):
                matched = True
                type_matched_files.append(indicator)

        # Check file patterns if no direct indicators found
        if not matched and "file_patterns" in rules:
            for pattern in rules["file_patterns"]:
                matching_files = _find_matching_files(pattern, all_files)
                if matching_files:
                    matched = True
                    type_matched_files.extend(matching_files)

        # Check required files if specified
        if rules.get("required_files"):
            if not all(f in files_set for f in rules["required_files"]):
                matched = False

        # Run additional checks if specified
        if matched and rules.get("additional_checks"):
            try:
                matched = all(
                    check(project_path) for check in rules["additional_checks"]
                )
            except Exception:
                matched = False

        # Update project type if this match has higher priority
        if matched and priority > max_priority:
            project_type = type_name
            max_priority = priority
            matched_files = type_matched_files

    # Detect language and framework
    language, framework = detect_language_and_framework(project_path)

    # If no specific type detected, check for common development patterns
    if project_type == "generic":
        project_type = _detect_generic_project_type(files_set, all_files)

    result: ProjectInfo = {
        "type": project_type,
        "language": language,
        "framework": framework,
        "description": PROJECT_TYPES.get(
            project_type, {"description": "Generic Project"}
        )["description"],
        "matched_files": matched_files,
        "path": project_path,
    }

    return result


def _get_generic_result() -> ProjectInfo:
    """Return a generic project result when type cannot be determined.

    Returns:
        ProjectInfo: Default project information for generic/unknown projects
    """
    return {
        "type": "generic",
        "language": "unknown",
        "framework": "none",
        "description": "Generic Project",
        "matched_files": [],
        "path": "",
    }


def _get_files_recursive(
    path: str, max_depth: int = 2, current_depth: int = 0
) -> set[str]:
    """Get all files recursively up to max_depth.

    Args:
        path: Directory path to scan
        max_depth: Maximum directory depth to traverse (default: 2)
        current_depth: Current traversal depth (used internally)

    Returns:
        Set[str]: Set of file paths relative to the root path

    Note:
        - Skips hidden directories
        - Handles permission errors gracefully
        - Returns empty set if path is inaccessible
    """
    if current_depth > max_depth:
        return set()

    try:
        files: set[str] = set()
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.is_file():
                    files.add(entry.name)
                elif entry.is_dir() and not entry.name.startswith("."):
                    subfiles = _get_files_recursive(
                        entry.path, max_depth, current_depth + 1
                    )
                    files.update(f"{entry.name}/{f}" for f in subfiles)
        return files
    except (PermissionError, OSError):
        return set()


def _check_indicator(indicator: str, files_set: set[str], all_files: set[str]) -> bool:
    """Check if an indicator matches any files in the project.

    Args:
        indicator: File pattern or name to check for
        files_set: Set of files in the root directory
        all_files: Set of all files in the project (including subdirectories)

    Returns:
        bool: True if the indicator matches any files, False otherwise

    Note:
        Handles both exact matches and glob patterns (using * wildcard)
    """
    if "*" in indicator:
        pattern = indicator.replace(".", "[.]").replace("*", ".*")
        return any(re.match(pattern + "$", f) for f in all_files)
    return indicator in files_set


def _find_matching_files(pattern: str, files: set[str]) -> list[str]:
    """Find files matching a given pattern.

    Args:
        pattern: File pattern to match against
        files: Set of files to search through

    Returns:
        List[str]: List of file names that match the pattern

    Note:
        Supports both exact matches and glob patterns (using * wildcard)
    """
    if "*" in pattern:
        pattern = pattern.replace(".", "[.]").replace("*", ".*")
        return [f for f in files if re.match(pattern + "$", f)]
    return [f for f in files if f == pattern]


def _detect_generic_project_type(files_set: set[str], all_files: set[str]) -> str:
    """Detect if a generic project has any common development patterns.

    Args:
        files_set: Set of files in the root directory
        all_files: Set of all files in the project (including subdirectories)

    Returns:
        str: 'generic_dev' if development patterns are found, 'generic' otherwise

    Note:
        Checks for common development indicators like:
        - Documentation files
        - Version control
        - Test directories
        - Configuration files
        - Build artifacts
    """
    dev_indicators = {
        "docs": ["README.md", "CONTRIBUTING.md", "docs/", "documentation/"],
        "vcs": [".git/", ".svn/", ".hg/"],
        "tests": ["test/", "tests/", "spec/", "specs/"],
        "config": [".env", "config/", "settings/"],
        "build": ["build/", "dist/", "target/"],
    }

    matched_categories = set()

    for category, indicators in dev_indicators.items():
        if any(
            ind in files_set or any(f.startswith(ind) for f in all_files)
            for ind in indicators
        ):
            matched_categories.add(category)

    return "generic_dev" if matched_categories else "generic"


def detect_language_and_framework(project_path: str) -> tuple[str, str]:
    """Detect the primary programming language and framework used in a project.

    Args:
        project_path: Path to the project directory

    Returns:
        Tuple[str, str]: A tuple containing:
            - Primary programming language (or 'unknown')
            - Framework name (or 'none')

    Note:
        - Language detection based on file extensions and key files
        - Framework detection based on dependency files and imports
        - Returns ('unknown', 'none') if detection fails or path is inaccessible
    """
    try:
        files = os.listdir(project_path)
    except:
        return "unknown", "none"

    # Language detection based on file extensions and key files
    language_indicators = {
        "python": [".py", "requirements.txt", "setup.py", "Pipfile"],
        "javascript": [".js", "package.json"],
        "typescript": [".ts", ".tsx", "tsconfig.json"],
        "kotlin": [".kt", "build.gradle.kts"],
        "php": [".php", "composer.json"],
        "swift": [".swift", "Package.swift"],
        "cpp": [".cpp", ".hpp", ".cc", ".cxx"],
        "c": [".c", ".h"],
        "csharp": [".cs", ".csproj", ".sln"],
        "java": [".java", "pom.xml", "build.gradle"],
        "go": [".go", "go.mod", "go.sum"],
        "ruby": [".rb", "Gemfile", "Rakefile"],
        "rust": [".rs", "Cargo.toml"],
        "dart": [".dart", "pubspec.yaml"],
        "scala": [".scala", "build.sbt"],
    }

    # Framework detection based on specific files/directories
    framework_indicators = {
        "django": ["manage.py", "django.contrib"],
        "flask": ["flask", "Flask=="],
        "fastapi": ["fastapi"],
        "react": ["react", "React."],
        "express": ["express"],
        "dotnet": ["Microsoft.NET.Sdk"],
        "qt": ["Qt.", "QtCore"],
        "gtk": ["gtk", "Gtk"],
        "unity": ["UnityEngine"],
        "unreal": ["UE4", "UE5"],
        "pytorch": ["torch", "pytorch"],
        "tensorflow": ["tensorflow"],
        "rails": ["rails", "Rails"],
        "spring": ["spring-boot", "SpringBoot"],
        "laravel": ["laravel", "Laravel"],
        "gin": ["gin-gonic/gin"],
        "flutter": ["flutter", "Flutter"],
        "angular": ["@angular/core"],
        "vue": ["vue", "Vue"],
        "svelte": ["svelte"],
        "next": ["next", "Next.js"],
        "nuxt": ["nuxt", "Nuxt.js"],
        "nest": ["@nestjs/core"],
        "fiber": ["fiber"],
        "echo": ["labstack/echo"],
        "rocket": ["rocket"],
        "actix": ["actix-web"],
        "axum": ["axum"],
        "sinatra": ["sinatra"],
        "hanami": ["hanami"],
        "play": ["play.api"],
        "akka": ["akka"],
        "ktor": ["ktor"],
        "micronaut": ["micronaut"],
        "quarkus": ["quarkus"],
        "helidon": ["helidon"],
    }

    # Detect language
    detected_language = "unknown"
    max_matches = 0

    for lang, indicators in language_indicators.items():
        matches = 0
        for f in files:
            if any(
                f.endswith(ind) if ind.startswith(".") else ind in f
                for ind in indicators
            ):
                matches += 1
        if matches > max_matches:
            max_matches = matches
            detected_language = lang

    # Detect framework by checking file contents
    detected_framework = "none"
    for framework, indicators in framework_indicators.items():
        for f in files:
            if f in ["requirements.txt", "package.json", "composer.json"]:
                try:
                    with open(os.path.join(project_path, f)) as file:
                        content = file.read().lower()
                        if any(ind.lower() in content for ind in indicators):
                            detected_framework = framework
                            break
                except:
                    continue

    return detected_language, detected_framework


def get_file_type_info(filename: str) -> tuple[str, str]:
    """Get file type information based on file extension.

    Args:
        filename: Name of the file to analyze

    Returns:
        Tuple[str, str]: A tuple containing:
            - File type name (e.g., 'Python Source', 'JavaScript')
            - Description of the file type and its purpose
    """
    ext = os.path.splitext(filename)[1].lower()

    type_map = {
        ".py": ("Python Source", "Python script containing project logic"),
        ".js": ("JavaScript", "JavaScript file for client-side functionality"),
        ".ts": ("TypeScript", "TypeScript source file"),
        ".tsx": ("TypeScript/React", "React component with TypeScript"),
        ".kt": ("Kotlin Source", "Kotlin implementation file"),
        ".php": ("PHP Source", "PHP script for server-side functionality"),
        ".swift": ("Swift Source", "Swift implementation file"),
        ".cpp": ("C++ Source", "C++ implementation file"),
        ".hpp": ("C++ Header", "C++ header file"),
        ".c": ("C Source", "C implementation file"),
        ".h": ("C/C++ Header", "Header file"),
        ".cs": ("C# Source", "C# implementation file"),
        ".csx": ("C# Script", "C# script file"),
    }

    return type_map.get(ext, ("Generic", "Project file"))


def scan_for_projects(
    root_path: str,
    max_depth: int = 3,
    ignored_dirs: list[str] | None = None,
    use_cache: bool = True,
) -> list[dict[str, str]]:
    """Scan directory recursively for projects with caching.

    Args:
        root_path: Root directory to start scanning from
        max_depth: Maximum directory depth to traverse (default: 3)
        ignored_dirs: List of directory names to ignore (default: None)
        use_cache: Whether to use cached results (default: True)

    Returns:
        List[Dict[str, str]]: List of dictionaries containing project information:
            - path: Project directory path
            - type: Detected project type
            - name: Project name
            - description: Project description
            - language: Primary programming language
            - framework: Detected framework

    Note:
        - Uses caching to improve performance on subsequent scans
        - Cache expires after CACHE_EXPIRATION seconds (default: 300)
        - Ignores directories specified in IGNORED_DIRECTORIES
    """
    cache_key = f"{root_path}:{max_depth}"

    # Check cache
    if use_cache and cache_key in _scan_cache:
        cache_time, cached_results = _scan_cache[cache_key]
        # Cache is valid for 5 minutes
        if time.time() - cache_time < CACHE_EXPIRATION:
            return cached_results

    # Perform scan as usual
    results = _do_scan(root_path, max_depth, ignored_dirs)

    # Save to cache
    if use_cache:
        _scan_cache[cache_key] = (time.time(), results)

    return results


def get_project_description(project_path: str) -> dict[str, str | list[str]]:
    """Get project description and key features using standardized approach.

    This function analyzes a project directory to generate a description and list of key features.
    It uses project type detection and standard patterns to create a consistent description format.

    Args:
        project_path: Path to the project root directory

    Returns:
        dict[str, Union[str, list[str]]]: Dictionary containing:
            - name (str): Project name derived from directory
            - description (str): Project directory structure and information
            - key_features (list[str]): List of key project features including:
                - Project type description
                - Primary language
                - Framework information
                - File and directory tracking
                - Automatic updates

    Raises:
        Exception: If there's an error detecting project type or analyzing features
    """
    try:
        project_info = detect_project_type(project_path)
        project_type = project_info["type"]

        result: dict[str, str | list[str]] = {
            "name": os.path.basename(project_path),
            "description": "Project directory structure and information",
            "key_features": [
                f"Type: {PROJECT_TYPES.get(project_type, {'description': 'Generic Project'})['description']}",
                f"Language: {project_info['language']}",
                f"Framework: {project_info['framework']}",
                "File and directory tracking",
                "Automatic updates",
            ],
        }

        return result

    except Exception as e:
        print(f"Error getting project description: {e}")
        return {
            "name": os.path.basename(project_path),
            "description": "Error reading project information",
            "key_features": ["File and directory tracking"],
        }


def _do_scan(
    root_path: str, max_depth: int = 3, ignored_dirs: list[str] | None = None
) -> list[dict[str, str]]:
    """Perform a scan of the directory to find projects.

    Args:
        root_path: Root directory to start scanning from
        max_depth: Maximum directory depth to traverse (default: 3)
        ignored_dirs: List of directory names to ignore (default: None)

    Returns:
        List[Dict[str, str]]: List of dictionaries containing project information:
            - path: Project directory path
            - type: Detected project type
            - name: Project name
            - description: Project description
            - language: Primary programming language
            - framework: Detected framework

    Note:
        - Checks root directory first before scanning subdirectories
        - Skips ignored directories and inaccessible paths
        - Uses project type detection with caching
    """
    if ignored_dirs is None:
        ignored_dirs = _config.get("ignored_directories", [])

    projects: list[dict[str, str]] = []
    root_path = os.path.abspath(root_path or ".")

    # Check the root directory first
    project_type = detect_project_type(root_path)
    if project_type != "generic":
        # Analyze project information
        project_info = get_project_description(root_path)
        language, framework = detect_language_and_framework(root_path)
        projects.append(
            {
                "path": root_path,
                "type": project_type,
                "name": project_info.get("name", os.path.basename(root_path)),
                "description": project_info.get(
                    "description", "No description available"
                ),
                "language": language,
                "framework": framework,
            }
        )

    def _scan_directory(current_path: str, current_depth: int) -> None:
        """Recursively scan directory for projects.

        Args:
            current_path: Current directory being scanned
            current_depth: Current depth in the directory tree

        Note:
            - Updates the outer projects list when projects are found
            - Skips ignored directories and inaccessible paths
            - Stops at max_depth
        """
        if current_depth > max_depth:
            return

        try:
            # Scan subdirectories
            for item in os.listdir(current_path):
                # Skip ignored directories immediately
                if item in IGNORED_DIRECTORIES:
                    continue

                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    # Check each subdirectory
                    project_type = detect_project_type(item_path)
                    if project_type != "generic":
                        # Analyze project information
                        project_info = get_project_description(item_path)
                        language, framework = detect_language_and_framework(item_path)
                        projects.append(
                            {
                                "path": item_path,
                                "type": project_type,
                                "name": project_info.get("name", item),
                                "description": project_info.get(
                                    "description", "No description available"
                                ),
                                "language": language,
                                "framework": framework,
                            }
                        )
                    else:
                        # If not a project, scan further
                        _scan_directory(item_path, current_depth + 1)

        except (PermissionError, OSError):
            # Skip directories we can't access
            pass

    # Start scanning from the root directory
    _scan_directory(root_path, 0)
    return projects

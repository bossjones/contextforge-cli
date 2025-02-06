#!/usr/bin/env python3
import argparse
import json
import logging
import os
from typing import Any, Dict, List, Optional, TypedDict

from contextforge_cli.vendored.cursorfocus.project_detector import scan_for_projects


class ProjectConfig(TypedDict):
    """Type definition for project configuration.

    Attributes:
        name: Project name
        project_path: Path to the project directory
        update_interval: Time between updates in seconds
        max_depth: Maximum directory depth to scan
    """

    name: str
    project_path: str
    update_interval: int
    max_depth: int


class Config(TypedDict):
    """Type definition for global configuration.

    Attributes:
        projects: List of project configurations
        ignored_directories: List of directory names to ignore
        ignored_files: List of file patterns to ignore
    """

    projects: list[ProjectConfig]
    ignored_directories: list[str]
    ignored_files: list[str]


def setup_cursorfocus() -> None:
    """Set up CursorFocus for your projects.

    This function is the main entry point for the CursorFocus setup utility.
    It handles command-line arguments for:
    - Adding/removing projects
    - Scanning directories for projects
    - Listing configured projects
    - Importing/exporting configurations
    - Updating project settings

    Note:
        Creates or updates a config.json file in the script directory.
    """
    parser = argparse.ArgumentParser(description="Set up CursorFocus for your projects")
    parser.add_argument(
        "--projects", "-p", nargs="+", help="Paths to projects to monitor"
    )
    parser.add_argument(
        "--names", "-n", nargs="+", help="Names for the projects (optional)"
    )
    parser.add_argument(
        "--list", "-l", action="store_true", help="List all configured projects"
    )
    parser.add_argument(
        "--remove",
        "-r",
        nargs="+",
        help='Remove projects by name/index, or use "all" to remove all projects',
    )
    parser.add_argument(
        "--scan", "-s", nargs="?", const=".", help="Scan directory for projects"
    )
    parser.add_argument(
        "--update-interval",
        "-u",
        type=int,
        help="Update interval in seconds for project(s)",
    )
    parser.add_argument(
        "--max-depth", "-d", type=int, help="Maximum directory depth for scanning"
    )
    parser.add_argument(
        "--info", "-i", help="Show detailed information about a project by name/index"
    )
    parser.add_argument("--export", "-e", help="Export configuration to a file")
    parser.add_argument(
        "--import", "-m", dest="import_file", help="Import configuration from a file"
    )

    args = parser.parse_args()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.json")
    config: Config = load_or_create_config(config_path)

    if "projects" not in config:
        config["projects"] = []

    if args.import_file:
        import_config(config, args.import_file)
        save_config(config_path, config)
        return

    if args.export:
        export_config(config, args.export)
        return

    if args.info:
        show_project_info(config["projects"], args.info)
        return

    if args.list:
        list_projects(config["projects"])
        return

    if args.remove:
        if "all" in args.remove:
            if confirm_action("Remove all projects?"):
                config["projects"] = []
                save_config(config_path, config)
                print("✅ All projects removed")
        else:
            remove_projects(config, args.remove)
            save_config(config_path, config)
        return

    # Handle scan option
    if args.scan is not None:
        scan_path = os.path.abspath(args.scan) if args.scan else os.getcwd()
        print(f"🔍 Scanning: {scan_path}")
        found_projects = scan_for_projects(scan_path, 3)

        if not found_projects:
            print("❌ No projects found")
            return

        print(f"\nFound {len(found_projects)} projects:")
        for i, project in enumerate(found_projects, 1):
            print(f"{i}. {project['name']} ({project['type']})")
            print(f"   Path: {project['path']}")
            if project.get("language"):
                print(f"   Language: {project['language']}")
            if project.get("framework"):
                print(f"   Framework: {project['framework']}")

        print("\nSelect projects (numbers/all/q):")
        try:
            selection = input("> ").strip().lower()
            if selection in ["q", "quit", "exit"]:
                return

            indices: list[int] = []
            if selection == "all":
                indices = list(range(len(found_projects)))
            else:
                try:
                    indices = [int(i) - 1 for i in selection.split()]
                    if any(i < 0 or i >= len(found_projects) for i in indices):
                        print("❌ Invalid numbers")
                        return
                except ValueError:
                    print("❌ Invalid input")
                    return

            added = 0
            for idx in indices:
                project = found_projects[idx]
                if not any(
                    p["project_path"] == project["path"] for p in config["projects"]
                ):
                    new_project: ProjectConfig = {
                        "name": project["name"],
                        "project_path": project["path"],
                        "update_interval": 60,
                        "max_depth": 3,
                    }
                    config["projects"].append(new_project)
                    added += 1

            if added > 0:
                print(f"✅ Added {added} projects")

        except KeyboardInterrupt:
            print("\n❌ Cancelled")
            return

        if config["projects"]:
            save_config(config_path, config)
        return

    # Add/update projects
    if args.projects:
        valid_projects: list[ProjectConfig] = []
        for i, project_path in enumerate(args.projects):
            abs_path = os.path.abspath(project_path)
            if not os.path.exists(abs_path):
                print(f"⚠️ Path not found: {abs_path}")
                continue

            project_name = (
                args.names[i]
                if args.names and i < len(args.names)
                else get_project_name(abs_path)
            )
            project_config: ProjectConfig = {
                "name": project_name,
                "project_path": abs_path,
                "update_interval": args.update_interval if args.update_interval else 60,
                "max_depth": args.max_depth if args.max_depth else 3,
            }
            valid_projects.append(project_config)

        names = [p["name"] for p in valid_projects]
        if len(names) != len(set(names)):
            name_counts: dict[str, int] = {}
            for project in valid_projects:
                base_name = project["name"]
                if base_name in name_counts:
                    name_counts[base_name] += 1
                    project["name"] = f"{base_name} ({name_counts[base_name]})"
                else:
                    name_counts[base_name] = 1

        for project in valid_projects:
            existing = next(
                (
                    p
                    for p in config["projects"]
                    if p["project_path"] == project["project_path"]
                ),
                None,
            )
            if existing:
                existing.update(project)
            else:
                config["projects"].append(project)

    save_config(config_path, config)
    print("\n📁 Projects:")
    for project in config["projects"]:
        print(f"\n• {project['name']}")
        print(f"  Path: {project['project_path']}")
        print(f"  Update: {project['update_interval']}s")
        print(f"  Depth: {project['max_depth']}")

    print(f"\nRun: python {os.path.join(script_dir, 'focus.py')}")


def load_or_create_config(config_path: str) -> Config:
    """Load existing config or create default one.

    Args:
        config_path: Path to the configuration file

    Returns:
        Config: Loaded configuration or default configuration if file doesn't exist
    """
    if os.path.exists(config_path):
        with open(config_path) as f:
            return json.load(f)
    return get_default_config()


def get_default_config() -> Config:
    """Return default configuration.

    Returns:
        Config: Default configuration with empty projects list and standard ignore patterns
    """
    return {
        "projects": [],
        "ignored_directories": [
            "__pycache__",
            "node_modules",
            "venv",
            ".git",
            ".idea",
            ".vscode",
            "dist",
            "build",
        ],
        "ignored_files": [".DS_Store", "*.pyc", "*.pyo"],
    }


def save_config(config_path: str, config: Config) -> None:
    """Save configuration to file.

    Args:
        config_path: Path where to save the configuration
        config: Configuration dictionary to save
    """
    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)


def list_projects(projects: list[ProjectConfig]) -> None:
    """Display list of configured projects.

    Args:
        projects: List of project configurations to display
    """
    if not projects:
        print("\n📁 No projects configured.")
        return

    print("\n📁 Configured projects:")
    for i, project in enumerate(projects, 1):
        print(f"\n  {i}. {project['name']}:")
        print(f"     Path: {project['project_path']}")
        print(f"     Update interval: {project['update_interval']} seconds")
        print(f"     Max depth: {project['max_depth']} levels")


def remove_projects(config: Config, targets: list[str]) -> None:
    """Remove specific projects by name or index.

    Args:
        config: Global configuration dictionary
        targets: List of project names or indices to remove
    """
    if not config["projects"]:
        print("\n⚠️ No projects configured.")
        return

    remaining_projects: list[ProjectConfig] = []
    removed: list[str] = []

    for project in config["projects"]:
        should_keep = True

        for target in targets:
            # Check if target is an index
            try:
                idx = int(target)
                if idx == config["projects"].index(project) + 1:
                    should_keep = False
                    removed.append(project["name"])
                    break
            except ValueError:
                # Target is a name
                if project["name"].lower() == target.lower():
                    should_keep = False
                    removed.append(project["name"])
                    break

        if should_keep:
            remaining_projects.append(project)

    if removed:
        config["projects"] = remaining_projects
        print(f"\n✅ Removed projects: {', '.join(removed)}")
    else:
        print("\n⚠️ No matching projects found.")


def confirm_action(message: str) -> bool:
    """Ask for user confirmation.

    Args:
        message: Message to display to the user

    Returns:
        bool: True if user confirms, False otherwise
    """
    while True:
        response = input(f"\n{message} (y/n): ").lower()
        if response in ["y", "yes"]:
            return True
        if response in ["n", "no"]:
            return False


def get_project_name(project_path: str) -> str:
    """Get project name from directory name, with some cleanup.

    Args:
        project_path: Path to the project directory

    Returns:
        str: Cleaned up project name in title case
    """
    # Get the base directory name
    base_name = os.path.basename(os.path.normpath(project_path))

    # Clean up common suffixes
    name = base_name.lower()
    for suffix in ["-main", "-master", "-dev", "-development", ".git", "-project"]:
        if name.endswith(suffix):
            base_name = base_name[: -len(suffix)]
            break

    # Convert to title case and replace special characters
    words = base_name.replace("-", " ").replace("_", " ").split()
    return " ".join(word.capitalize() for word in words)


def show_project_info(projects: list[ProjectConfig], target: str) -> None:
    """Display detailed information about a specific project.

    Args:
        projects: List of project configurations
        target: Project name or index to show information for
    """
    if not projects:
        print("\n⚠️ No projects configured.")
        return

    project = None
    try:
        # Try to use target as index
        idx = int(target) - 1
        if 0 <= idx < len(projects):
            project = projects[idx]
    except ValueError:
        # Use target as name
        project = next(
            (p for p in projects if p["name"].lower() == target.lower()), None
        )

    if not project:
        print(f"\n❌ Project not found: {target}")
        return

    print(f"\n📁 Project Details: {project['name']}")
    print(f"  Path: {project['project_path']}")
    print(f"  Update Interval: {project['update_interval']} seconds")
    print(f"  Max Depth: {project['max_depth']} levels")

    # Show additional project info if available
    project_type = detect_project_type(project["project_path"])
    if project_type:
        print(f"  Type: {project_type['type']}")
        if project_type.get("language"):
            print(f"  Language: {project_type['language']}")
        if project_type.get("framework"):
            print(f"  Framework: {project_type['framework']}")


def export_config(config: Config, export_path: str) -> None:
    """Export configuration to a file.

    Args:
        config: Configuration to export
        export_path: Path where to save the exported configuration
    """
    try:
        with open(export_path, "w") as f:
            json.dump(config, f, indent=4)
        print(f"\n✅ Configuration exported to: {export_path}")
    except Exception as e:
        print(f"\n❌ Failed to export configuration: {str(e)}")


def import_config(config: Config, import_path: str) -> None:
    """Import configuration from a file.

    Args:
        config: Current configuration to update
        import_path: Path to the configuration file to import
    """
    try:
        with open(import_path) as f:
            imported: Config = json.load(f)

        if "projects" in imported:
            # Validate and update paths
            valid_projects: list[ProjectConfig] = []
            for project in imported["projects"]:
                if all(
                    key in project
                    for key in ["name", "project_path", "update_interval", "max_depth"]
                ):
                    if os.path.exists(project["project_path"]):
                        valid_projects.append(project)
                    else:
                        print(
                            f"\n⚠️ Skipping project with invalid path: {project['name']}"
                        )

            config["projects"] = valid_projects
            print(f"\n✅ Imported {len(valid_projects)} projects")

        # Import other settings
        for key in ["ignored_directories", "ignored_files"]:
            if key in imported:
                config[key] = imported[key]

    except Exception as e:
        print(f"\n❌ Failed to import configuration: {str(e)}")


def detect_project_type(project_path: str) -> dict[str, Any] | None:
    """Detect project type using project_detector.

    Args:
        project_path: Path to the project directory

    Returns:
        Optional[Dict[str, Any]]: Project type information if detected, None otherwise
    """
    try:
        projects = scan_for_projects(project_path, 1)
        return projects[0] if projects else None
    except:
        return None


if __name__ == "__main__":
    setup_cursorfocus()

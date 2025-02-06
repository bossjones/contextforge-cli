import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

from contextforge_cli.vendored.cursorfocus.auto_updater import AutoUpdater
from contextforge_cli.vendored.cursorfocus.config import get_default_config, load_config
from contextforge_cli.vendored.cursorfocus.content_generator import (
    generate_focus_content,
)
from contextforge_cli.vendored.cursorfocus.rules_analyzer import RulesAnalyzer
from contextforge_cli.vendored.cursorfocus.rules_generator import RulesGenerator
from contextforge_cli.vendored.cursorfocus.rules_watcher import ProjectWatcherManager


def retry_generate_rules(
    project_path: str, project_name: str, max_retries: int = 3
) -> str | None:
    """Retry generating rules file automatically with exponential backoff.

    Attempts to generate a rules file for the project, retrying on failure with
    increasing delays between attempts.

    Args:
        project_path: Path to the project root directory
        project_name: Name of the project for display purposes
        max_retries: Maximum number of retry attempts (default: 3)

    Returns:
        Optional[str]: Path to the generated rules file if successful,
            None if all retries failed

    Raises:
        Exception: If all retry attempts fail

    Note:
        - Uses exponential backoff between retries (2^n seconds)
        - Prompts user to choose between JSON and Markdown format
        - Displays progress and error information during retries
    """
    retries = 0
    while retries < max_retries:
        try:
            print(f"\n📄 Analyzing: {project_path}")
            analyzer = RulesAnalyzer(project_path)
            project_info = analyzer.analyze_project_for_rules()

            # Ask for format preference using numbers
            print("\nSelect format for .cursorrules file:")
            print("1. JSON")
            print("2. Markdown")
            while True:
                try:
                    choice = int(input("Enter selection (1-2): "))
                    if choice in [1, 2]:
                        format_choice = "json" if choice == 1 else "markdown"
                        break
                    print("Please enter 1 or 2")
                except ValueError:
                    print("Please enter a number")

            rules_generator = RulesGenerator(project_path)
            rules_file = rules_generator.generate_rules_file(
                project_info, format=format_choice
            )
            print(f"✓ {os.path.basename(rules_file)}")
            return rules_file
        except Exception as e:
            retries += 1
            if retries < max_retries:
                wait_time = 2 * (2 ** (retries - 1))  # Exponential backoff
                print(
                    f"\n⚠️ Error occurred, automatically retrying in {wait_time} seconds... (attempt {retries}/{max_retries})"
                )
                print(f"Error details: {str(e)}")
                time.sleep(wait_time)
                continue
            else:
                print(
                    f"\n❌ Failed to generate rules after {max_retries} attempts: {e}"
                )
                raise


def setup_cursor_focus(project_path: str, project_name: str | None = None) -> None:
    """Set up CursorFocus for a project by generating or updating necessary files.

    This function handles the initial setup or update of CursorFocus configuration files
    for a project. It manages both the rules file and Focus.md generation.

    Args:
        project_path: Path to the project root directory
        project_name: Optional name of the project for display purposes.
            If not provided, will use generic "project" in messages.

    Returns:
        None

    Raises:
        Exception: If setup fails for any reason (file generation, writing, etc.)

    Note:
        - Checks for existing .cursorrules file and prompts for update
        - Generates new rules file with retry mechanism
        - Creates initial Focus.md using default configuration
    """
    try:
        # Check for existing rules file
        rules_file = os.path.join(project_path, ".cursorrules")

        if os.path.exists(rules_file):
            print(f"\nRules file exists for {project_name or 'project'}")
            response = input("Update rules? (y/n): ").lower()
            if response != "y":
                return

        # Generate/Update .cursorrules file with retry mechanism
        rules_file = retry_generate_rules(project_path, project_name)

        # Generate initial Focus.md with default config
        focus_file = os.path.join(project_path, "Focus.md")
        default_config = get_default_config()
        content = generate_focus_content(project_path, default_config)
        with open(focus_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✓ {os.path.basename(focus_file)}")

    except Exception as e:
        print(f"❌ Setup error: {e}")
        raise


def monitor_project(
    project_config: dict[str, Any], global_config: dict[str, Any]
) -> None:
    """Monitor a single project for changes and update Focus.md accordingly.

    This function continuously monitors a project directory for changes and updates
    the Focus.md file when changes are detected. It also manages the rules watcher
    for the project.

    Args:
        project_config: Project-specific configuration dictionary containing:
            - project_path: Path to project directory
            - name: Project name
            - update_interval: Time between checks (optional)
            - Other project-specific settings
        global_config: Global configuration dictionary that applies to all projects

    Returns:
        None

    Note:
        - Runs indefinitely until interrupted
        - Updates Focus.md only when content changes
        - Uses project-specific update interval from config
        - Merges project config with global config
    """
    project_path = project_config["project_path"]
    project_name = project_config["name"]
    print(f"👀 {project_name}")

    # Merge project config with global config
    config = {**global_config, **project_config}

    focus_file = os.path.join(project_path, "Focus.md")
    last_content = None
    last_update = 0

    # Start rules watcher for this project
    watcher = ProjectWatcherManager()
    watcher.add_project(project_path, project_name)

    while True:
        current_time = time.time()

        if current_time - last_update < config.get("update_interval", 60):
            time.sleep(1)
            continue

        content = generate_focus_content(project_path, config)

        if content != last_content:
            try:
                with open(focus_file, "w", encoding="utf-8") as f:
                    f.write(content)
                last_content = content
                print(f"✓ {project_name} ({datetime.now().strftime('%H:%M')})")
            except Exception as e:
                print(f"❌ {project_name}: {e}")

        last_update = current_time


def main() -> None:
    """Main entry point for CursorFocus application.

    This function handles the overall application flow including:
    - Checking for and applying updates
    - Loading configuration
    - Setting up projects
    - Starting monitoring threads for each project

    Returns:
        None

    Note:
        - Checks for updates before starting
        - Uses default config if no config.json found
        - Monitors multiple projects concurrently using threads
        - Runs until interrupted with Ctrl+C
        - All monitoring threads are daemonized
    """
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

    # Check updates
    print("\n🔄 Checking updates...")
    updater = AutoUpdater()
    update_info = updater.check_for_updates()

    if update_info:
        print(f"📦 Update available: {update_info['message']}")
        print(f"🕒 Date: {update_info['date']}")
        print(f"👤 Author: {update_info['author']}")
        try:
            if input("Update now? (y/n): ").lower() == "y":
                print("⏳ Downloading...")
                if updater.update(update_info):
                    print("✅ Updated! Please restart")
                    return
                else:
                    print("❌ Update failed")
        except KeyboardInterrupt:
            print("\n👋 Update canceled")
            pass
    else:
        print("✓ Latest version")

    config = load_config()
    if not config:
        print("No config.json found, using default configuration")
        config = get_default_config()

    if "projects" not in config:
        config["projects"] = [
            {
                "name": "Default Project",
                "project_path": config.get(
                    "project_path",
                    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
                ),
                "update_interval": config.get("update_interval", 60),
                "max_depth": config.get("max_depth", 3),
            }
        ]

    from threading import Thread

    threads = []

    try:
        # Setup projects
        for project in config["projects"]:
            if os.path.exists(project["project_path"]):
                setup_cursor_focus(project["project_path"], project["name"])
            else:
                print(f"⚠️ Not found: {project['project_path']}")
                continue

        # Start monitoring
        for project in config["projects"]:
            if os.path.exists(project["project_path"]):
                thread = Thread(
                    target=monitor_project, args=(project, config), daemon=True
                )
                thread.start()
                threads.append(thread)

        if not threads:
            print("❌ No projects to monitor")
            return

        print(f"\n📝 Monitoring {len(threads)} projects (Ctrl+C to stop)")

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n👋 Bye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()

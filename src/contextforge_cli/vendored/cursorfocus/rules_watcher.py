import os
import time
from typing import Any, Dict, Optional, Union

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from contextforge_cli.vendored.cursorfocus.project_detector import detect_project_type
from contextforge_cli.vendored.cursorfocus.rules_generator import RulesGenerator


class RulesWatcher(FileSystemEventHandler):
    """File system event handler for monitoring project changes and updating rules.

    This class watches for file changes in a project directory and automatically
    updates the .cursorrules file when relevant changes are detected.

    Attributes:
        project_path: Path to the project root directory
        project_id: Unique identifier for the project
        rules_generator: Instance of RulesGenerator for this project
        last_update: Timestamp of last update
        update_delay: Minimum seconds between updates
        auto_update: Whether to automatically update rules on changes
    """

    def __init__(self, project_path: str, project_id: str) -> None:
        """Initialize the RulesWatcher.

        Args:
            project_path: Path to the project root directory
            project_id: Unique identifier for the project
        """
        self.project_path: str = project_path
        self.project_id: str = project_id
        self.rules_generator: RulesGenerator = RulesGenerator(project_path)
        self.last_update: float = 0
        self.update_delay: int = 5  # Seconds to wait before updating
        self.auto_update: bool = False  # Disable auto-update by default

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events.

        Args:
            event: File system event containing modified file information

        Note:
            Only processes changes to Focus.md and project configuration files
            when auto-update is enabled and update_delay has elapsed.
        """
        if event.is_directory or not self.auto_update:
            return

        # Only process Focus.md changes or project configuration files
        if not self._should_process_file(event.src_path):
            return

        current_time = time.time()
        if current_time - self.last_update < self.update_delay:
            return

        self.last_update = current_time
        self._update_rules()

    def _should_process_file(self, file_path: str) -> bool:
        """Check if the file change should trigger a rules update.

        Args:
            file_path: Path to the modified file

        Returns:
            bool: True if the file should trigger an update, False otherwise

        Note:
            Only processes specific file types like Focus.md, package.json,
            requirements.txt, etc. that indicate project configuration changes.
        """
        if not self.auto_update:
            return False

        filename = os.path.basename(file_path)

        # List of files that should trigger an update
        trigger_files = [
            "Focus.md",
            "package.json",
            "requirements.txt",
            "CMakeLists.txt",
            ".csproj",
            "composer.json",
            "build.gradle",
            "pom.xml",
        ]

        return filename in trigger_files or any(
            file_path.endswith(ext) for ext in [".csproj"]
        )

    def _update_rules(self) -> None:
        """Update the .cursorrules file.

        Attempts to re-detect project type and generate new rules.
        Logs success or failure of the update operation.

        Note:
            Only executes if auto_update is enabled.
        """
        if not self.auto_update:
            return

        try:
            # Re-detect project type
            project_info = detect_project_type(self.project_path)

            # Generate new rules
            self.rules_generator.generate_rules_file(project_info)
            print(
                f"Updated .cursorrules for project {self.project_id} at {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        except Exception as e:
            print(f"Error updating .cursorrules for project {self.project_id}: {e}")

    def set_auto_update(self, enabled: bool) -> None:
        """Enable or disable auto-update of .cursorrules.

        Args:
            enabled: Whether to enable auto-update

        Note:
            When enabled, the watcher will automatically update rules
            when relevant project files change.
        """
        self.auto_update = enabled
        status = "enabled" if enabled else "disabled"
        print(
            f"Auto-update of .cursorrules is now {status} for project {self.project_id}"
        )


class ProjectWatcherManager:
    """Manager for multiple project watchers.

    This class manages multiple RulesWatcher instances, allowing for
    concurrent monitoring of multiple projects.

    Attributes:
        observers: Dictionary mapping project IDs to Observer instances
        watchers: Dictionary mapping project IDs to RulesWatcher instances
    """

    def __init__(self) -> None:
        """Initialize the ProjectWatcherManager."""
        self.observers: dict[str, Observer] = {}
        self.watchers: dict[str, RulesWatcher] = {}

    def add_project(self, project_path: str, project_id: str | None = None) -> str:
        """Add a new project to watch.

        Args:
            project_path: Path to the project root directory
            project_id: Optional unique identifier for the project.
                       If not provided, uses absolute path.

        Returns:
            str: Project ID of the added project

        Raises:
            ValueError: If project path does not exist
        """
        if not os.path.exists(project_path):
            raise ValueError(f"Project path does not exist: {project_path}")

        project_id = project_id or os.path.abspath(project_path)

        if project_id in self.observers:
            print(f"Project {project_id} is already being watched")
            return project_id

        event_handler = RulesWatcher(project_path, project_id)
        observer = Observer()
        observer.schedule(event_handler, project_path, recursive=True)
        observer.start()

        self.observers[project_id] = observer
        self.watchers[project_id] = event_handler

        print(f"Started watching project {project_id}")
        return project_id

    def remove_project(self, project_id: str) -> None:
        """Stop watching a project.

        Args:
            project_id: ID of the project to stop watching

        Note:
            Stops and removes both the observer and watcher for the project.
            Prints a message if the project is not being watched.
        """
        if project_id not in self.observers:
            print(f"Project {project_id} is not being watched")
            return

        observer = self.observers[project_id]
        observer.stop()
        observer.join()

        del self.observers[project_id]
        del self.watchers[project_id]

        print(f"Stopped watching project {project_id}")

    def list_projects(self) -> dict[str, str]:
        """Return a dictionary of watched projects and their paths.

        Returns:
            dict[str, str]: Dictionary mapping project IDs to their paths
        """
        return {pid: watcher.project_path for pid, watcher in self.watchers.items()}

    def stop_all(self) -> None:
        """Stop watching all projects.

        Stops and removes all observers and watchers.
        """
        for project_id in list(self.observers.keys()):
            self.remove_project(project_id)

    def set_auto_update(self, project_id: str, enabled: bool) -> None:
        """Enable or disable auto-update for a specific project.

        Args:
            project_id: ID of the project to configure
            enabled: Whether to enable auto-update

        Note:
            Prints a message if the project is not being watched.
        """
        if project_id in self.watchers:
            self.watchers[project_id].set_auto_update(enabled)
        else:
            print(f"Project {project_id} is not being watched")


def start_watching(project_paths: str | list[str]) -> None:
    """Start watching one or multiple project directories for changes.

    Args:
        project_paths: Single project path or list of project paths to watch

    Note:
        Runs indefinitely until interrupted with KeyboardInterrupt.
        Automatically stops all watchers on exit.
    """
    manager = ProjectWatcherManager()

    if isinstance(project_paths, str):
        project_paths = [project_paths]

    for path in project_paths:
        manager.add_project(path)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_all()

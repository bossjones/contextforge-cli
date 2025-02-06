import json
import logging
import os
import shutil
import tempfile
import zipfile
from datetime import UTC, datetime, timezone
from typing import Any, Dict, NoReturn, Optional

import requests


def clear_console() -> None:
    """Clear the console screen based on the operating system.

    This function uses the appropriate system command to clear the terminal screen
    based on the operating system - 'cls' for Windows and 'clear' for Unix-based systems.

    Returns:
        None
    """
    # For Windows
    if os.name == "nt":
        os.system("cls")
    # For Unix/Linux/MacOS
    else:
        os.system("clear")


class AutoUpdater:
    """A class to handle automatic updates from a GitHub repository.

    This class provides functionality to check for updates, compare versions,
    and download/install updates from a specified GitHub repository.

    Attributes:
        repo_url: The GitHub repository URL to check for updates.
        api_url: The corresponding GitHub API URL for the repository.
    """

    def __init__(
        self, repo_url: str = "https://github.com/RenjiYuusei/CursorFocus"
    ) -> None:
        """Initialize the AutoUpdater with a GitHub repository URL.

        Args:
            repo_url: The GitHub repository URL to check for updates.
                     Defaults to "https://github.com/RenjiYuusei/CursorFocus".
        """
        self.repo_url: str = repo_url
        self.api_url: str = repo_url.replace("github.com", "api.github.com/repos")

    def check_for_updates(self) -> dict[str, Any] | None:
        """Check for available updates from the GitHub repository.

        This method compares the current commit SHA with the latest commit in the repository.
        If an update is available, it returns information about the new version.

        Returns:
            Optional[Dict[str, Any]]: A dictionary containing update information if available:
                - sha: The commit SHA
                - message: The commit message
                - date: Formatted date of the commit
                - author: Name of the commit author
                - download_url: URL to download the update
                Returns None if no update is available or if an error occurs.

        Note:
            The method attempts to check both 'main' and 'master' branches if necessary.
        """
        try:
            # Check commit latest
            response = requests.get(f"{self.api_url}/commits/main")
            if response.status_code == 404:
                response = requests.get(f"{self.api_url}/commits/master")

            if response.status_code != 200:
                return None

            latest_commit = response.json()
            current_commit = self._get_current_commit()

            if latest_commit["sha"] != current_commit:
                # Convert UTC time to local time
                utc_date = datetime.strptime(
                    latest_commit["commit"]["author"]["date"], "%Y-%m-%dT%H:%M:%SZ"
                )
                local_date = utc_date.replace(tzinfo=UTC).astimezone(tz=None)
                formatted_date = local_date.strftime("%B %d, %Y at %I:%M %p")

                return {
                    "sha": latest_commit["sha"],
                    "message": latest_commit["commit"]["message"],
                    "date": formatted_date,
                    "author": latest_commit["commit"]["author"]["name"],
                    "download_url": f"{self.repo_url}/archive/refs/heads/main.zip",
                }

            return None

        except Exception as e:
            logging.error(f"Error checking for updates: {e}")
            return None

    def _get_current_commit(self) -> str:
        """Get the SHA of the current commit from the local file.

        This method reads the commit SHA from a local file named '.current_commit'.
        If the file doesn't exist or can't be read, returns an empty string.

        Returns:
            str: The current commit SHA if available, empty string otherwise.
        """
        try:
            version_file = os.path.join(os.path.dirname(__file__), ".current_commit")
            if os.path.exists(version_file):
                with open(version_file) as f:
                    return f.read().strip()
            return ""
        except:
            return ""

    def update(self, update_info: dict[str, Any]) -> bool:
        """Update the application with the latest version from GitHub.

        Downloads and installs the latest version of the application from the GitHub repository.
        The update process includes:
        1. Downloading the repository as a zip file
        2. Extracting the contents
        3. Copying new files to the installation directory
        4. Updating the current commit SHA
        5. Cleaning up temporary files

        Args:
            update_info: Dictionary containing update information:
                - download_url: URL to download the update zip
                - sha: The new commit SHA to save

        Returns:
            bool: True if update was successful, False otherwise.

        Note:
            The function will log any errors that occur during the update process.
        """
        try:
            # Download zip file of branch
            response = requests.get(update_info["download_url"])
            if response.status_code != 200:
                return False

            # Save zip file temporarily
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "update.zip")
            with open(zip_path, "wb") as f:
                f.write(response.content)

            # Unzip and update
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Get root directory name in zip
                root_dir = zip_ref.namelist()[0].split("/")[0]
                zip_ref.extractall(temp_dir)

                # Copy new files
                src_dir = os.path.join(temp_dir, root_dir)
                dst_dir = os.path.dirname(__file__)

                for item in os.listdir(src_dir):
                    s = os.path.join(src_dir, item)
                    d = os.path.join(dst_dir, item)
                    if os.path.isfile(s):
                        shutil.copy2(s, d)
                    elif os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)

            # Save SHA of new commit
            with open(os.path.join(dst_dir, ".current_commit"), "w") as f:
                f.write(update_info["sha"])

            # Clean up
            shutil.rmtree(temp_dir)

            # Clear console after successful update
            clear_console()
            return True

        except Exception as e:
            logging.error(f"Error updating: {e}")
            return False

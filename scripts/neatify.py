#!/usr/bin/env python3
# SOURCE: https://medium.com/pythoneers/18-insanely-useful-python-automation-scripts-i-use-everyday-b3aeb7671ce9

"""
Is your download folder a chaotic mess?
Do you find yourself scrambling to locate crucial files when you need them most?
Have you attempted folder organization countless times, only to fall short?

This all-in-one automation script transforms how you organize and manage your files in just minutes! Simply provide the path to the folder you want to clean up, and the script will work its magic.

File Extension Sorting: Automatically categorize all files into separate folders based on their file extensions for a more organized structure.
Duplicate File Removal: Detect and remove duplicate files by comparing their hashes, ensuring no redundant copies clog up your storage.
Date-Based Organization: Arrange files into folders based on their creation or last-modified dates, making it easy to locate files by period.
With this dual-purpose tool, you get a clean, logical file structure free of duplicates and organized by type and time. Efficiency has never been this seamless!
"""

import os
import shutil
import hashlib
from datetime import datetime
from typing import Dict, List, Optional

def get_file_hash(file_path: str) -> str:
    """Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        str: Hexadecimal representation of the file's SHA-256 hash.

    Raises:
        IOError: If the file cannot be read.
        FileNotFoundError: If the file does not exist.
    """
    with open(file_path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def organize_by_date_and_extension(folder_path: str) -> None:
    """Organize files by date, then by extension, and handle duplicates.

    This function:
    1. Creates a _Duplicates folder at the root directory
    2. Processes all files in the given directory
    3. Organizes files by modification date
    4. Further organizes files by extension within date folders
    5. Detects and moves duplicate files to the _Duplicates folder

    Args:
        folder_path: Path to the folder to organize.

    Raises:
        OSError: If there are permission or path issues.
        FileNotFoundError: If the folder path does not exist.
    """
    # Create a "Duplicates" folder at the root directory
    duplicates_folder = os.path.join(folder_path, '_Duplicates')
    os.makedirs(duplicates_folder, exist_ok=True)

    # Dictionary to store file hashes for duplicate detection
    file_hashes: dict[str, str] = {}

    # Iterate over all files in the directory
    all_files: list[str] = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                           if os.path.isfile(os.path.join(folder_path, f))]

    for file_path in all_files:
        # Get the modification date of the file
        modification_time: float = os.path.getmtime(file_path)
        modification_date: str = datetime.fromtimestamp(modification_time).strftime('%Y-%m-%d')

        # Create a folder for the modification date if it doesn't exist
        date_folder: str = os.path.join(folder_path, modification_date)
        os.makedirs(date_folder, exist_ok=True)

        # Calculate the file hash
        file_hash: str = get_file_hash(file_path)

        # Check for duplicates
        if file_hash in file_hashes:
            # File is a duplicate, move to "Duplicates" folder
            shutil.move(file_path, os.path.join(duplicates_folder, os.path.basename(file_path)))
            print(f"Moved duplicate file {os.path.basename(file_path)} to Duplicates folder.")
        else:
            # Store the file hash to prevent future duplicates
            file_hashes[file_hash] = file_path

            # Move the file to the date folder
            new_path: str = os.path.join(date_folder, os.path.basename(file_path))
            shutil.move(file_path, new_path)

            # Organize files within the date folder by extension
            _, extension = os.path.splitext(new_path)
            extension = extension.lower()
            extension_folder: str = os.path.join(date_folder, extension[1:])  # Remove the dot from extension
            os.makedirs(extension_folder, exist_ok=True)

            # Move the file to its extension-specific folder
            shutil.move(new_path, os.path.join(extension_folder, os.path.basename(new_path)))
            print(f"Moved {os.path.basename(new_path)} to {extension_folder}.")

    print("Files organized by date, extension, and duplicates handled successfully!")

if __name__ == "__main__":
    # Specify the directory to organize
    folder_path: str = input("Enter the path to the folder to organize: ")
    organize_by_date_and_extension(folder_path)

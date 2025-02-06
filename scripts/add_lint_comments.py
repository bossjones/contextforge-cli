#!/usr/bin/env python3

import subprocess
import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='Prepend pylint/pyright comments to Python files with specific imports')
    parser.add_argument('--dir', default='.', help='Directory to search')
    parser.add_argument('--dry-run', action='store_true', help='Show which files would be modified without making changes')
    return parser.parse_args()

PREPEND_LINES = """# pylint: disable=no-member
# pylint: disable=no-name-in-module
# pylint: disable=no-value-for-parameter
# pylint: disable=possibly-used-before-assignment
# pyright: reportAttributeAccessIssue=false
# pyright: reportInvalidTypeForm=false
# pyright: reportMissingTypeStubs=false
# pyright: reportUndefinedVariable=false
"""

def should_prepend(file_path, text):
    with open(file_path, encoding='utf-8') as file:
        first_lines = ''.join(file.readline() for _ in range(text.count('\n')))
        return text not in first_lines

def prepend_to_file(file_path, text):
    # Read original content
    with open(file_path, encoding='utf-8') as file:
        content = file.read()

    # Write to temporary file
    temp_path = file_path + '.tmp'
    with open(temp_path, 'w', encoding='utf-8') as file:
        file.write(text + content)

    # Replace original with temporary file
    os.replace(temp_path, file_path)

def main():
    args = parse_args()

    rg_command = [
        "rg",
        "-t", "py",
        "^\\s*(from|import)\\s+(discord|pydantic|pydantic_settings|dpytest)",
        "--files-with-matches",
        args.dir
    ]

    try:
        result = subprocess.run(rg_command, capture_output=True, text=True, check=True)
        files = [f for f in result.stdout.strip().split('\n') if f]

        if not files:
            print("No matching files found.")
            return

        print(f"Found {len(files)} matching files.")

        for file_path in files:
            try:
                if not os.path.isfile(file_path):
                    print(f"Skipping {file_path}: not a regular file")
                    continue

                if should_prepend(file_path, PREPEND_LINES):
                    if args.dry_run:
                        print(f"Would prepend to: {file_path}")
                    else:
                        prepend_to_file(file_path, PREPEND_LINES)
                        print(f"Prepended lines to: {file_path}")
                else:
                    print(f"Skipping {file_path}: already contains prepend lines")

            except PermissionError:
                print(f"Error: No permission to modify {file_path}")
            except OSError as e:
                print(f"Error processing {file_path}: {e}")

    except FileNotFoundError:
        print("Error: 'rg' (ripgrep) command not found. Please ensure ripgrep is installed.")
    except subprocess.CalledProcessError as e:
        print(f"Error running ripgrep: {e.stderr}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    main()

#!/usr/bin/env bash

set -euo pipefail

# Change to the root directory of the git repository
cd "$(git rev-parse --show-toplevel)"

# Get the current branch name
current_branch=$(git rev-parse --abbrev-ref HEAD)

# Create the diffs directory if it doesn't exist
mkdir -p diffs

# Function to process files and directories
process_item() {
    local item="$1"
    local rel_path="${item#./}"  # Remove leading './' if present

    # Check if the item is inside the contextforge_cli directory and not ignored by git
    if [[ "$rel_path" == contextforge_cli/* ]] && ! git check-ignore -q "$item" && [[ "$rel_path" != "uv.lock" && "$rel_path" != *.log && "$rel_path" != "logic-to-merge.md" ]]; then
        # Create the directory structure in the diffs folder
        mkdir -p "diffs/$(dirname "$rel_path")"

        # Run git diff and save the output
        if ! git diff main..$current_branch -- "$item" > "diffs/$rel_path.diff"; then
            echo "Error: Failed to diff $item" >&2
            return 1
        fi

        # If the diff is empty, remove the file
        if [ ! -s "diffs/$rel_path.diff" ]; then
            rm "diffs/$rel_path.diff"
        fi
    fi
}

# Use find to recursively process all files and directories within contextforge_cli
find ./contextforge_cli -type f -print0 | while IFS= read -r -d '' item; do
    echo "running process_item on $item"
    process_item "$item"
done

echo "Diff files have been saved in the 'diffs' directory."

# Run files-to-prompt on the generated diffs
# uv run files-to-prompt diffs/contextforge_cli --cxml -o diffs.xml

./process_diffs.sh

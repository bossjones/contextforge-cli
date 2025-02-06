#!/usr/bin/env bash
# shellcheck disable=SC2096
# shellcheck disable=SC3010
# NOTE: If you want to run the script without deleting any directories, set the DRY_RUN_REGENERATE_CASSETTES environment variable to 1

# Find all cassettes directories and store them in an array
# SOURCE: https://www.geeksforgeeks.org/mapfile-command-in-linux-with-examples/
declare -a cassette_dirs=($(find tests/* -type d -name "*cassettes*" -print))

# Sort the array uniquely
declare -a sorted_unique_cassette_dirs=($(printf "%s\n" "${cassette_dirs[@]}" | sort -u))

# Print the directories that will be deleted
echo

echo "The following directories will be deleted:"
for dir in "${sorted_unique_cassette_dirs[@]}"; do
    echo "$dir"
done

echo

# Prompt the user for confirmation
read -p "Do you want to proceed? (yes/no): " response

# Convert the response to lowercase
response=$(echo "$response" | tr '[:upper:]' '[:lower:]')

# Check the user's response
if [[ "$response" == "yes" ]]; then
    echo "Proceeding with deletion..."
    # Delete the directories
    if [[ "$DRY_RUN_REGENERATE_CASSETTES" = 1 ]]; then
        echo "would run: "
        echo 'find tests/* -type d -name "*cassettes*" -print0 | xargs -0 -I {} rm -rv {}'
        echo
    else
        find tests/* -type d -name "*cassettes*" -print0 | xargs -0 -I {} rm -rv {}
        echo
    fi
    echo "Deletion complete."
    echo
elif [[ "$response" == "no" ]]; then
    echo "Operation cancelled. No directories were deleted."
else
    echo "Invalid input. Please enter yes or no. Exiting without any changes."
fi

#!/bin/zsh

# Check if an argument is provided
if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <file_path>"
    exit 1
fi

# Get the input file path
input_file="$1"

# Extract the relative path from the input
relative_path="${input_file#*/contextforge-cli/}"

# Construct the comparison path by replacing 'contextforge-cli' with 'contextforge-cli-main'
compare_file="${input_file/contextforge-cli/contextforge-cli-main}"

# Perform the diff
if [[ -f "$input_file" && -f "$compare_file" ]]; then
    diff "$input_file" "$compare_file"
else
    echo "Error: One or both files do not exist:"
    echo "Source: $input_file"
    echo "Target: $compare_file"
    exit 1
fi

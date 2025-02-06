#!/usr/bin/env bash
# shellcheck shell=bash
# SOURCE: https://github.com/microsoft/CyberBattleSim/blob/main/createstubs.sh
# write a description of the script here
# This script generates type stubs for the installed packages using pyright.
# See pyright documentation for more information: https://microsoft.github.io/pyright/#/command-line

set -e

echo "$(tput setaf 2)Creating type stubs$(tput sgr0)"

echo 'Creating stubs'

mkdir -p typings/ || true

# uv run pyright -p pyproject.toml . | grep "Stub file not found for" | sed -n 's/.*Stub file not found for "\([^"]*\)".*/\1/p' | sed -n '/\./ s/\([^.]*\)\..*/\1/p' | sort | uniq | xargs -I {} echo "uv run pyright --createstub {}"
uv run pyright -p pyproject.toml . | grep "Stub file not found for" | sed -n 's/.*Stub file not found for "\([^"]*\)".*/\1/p' | sort | uniq | xargs -I {} echo "uv run pyright --createstub {}"

# Prompt the user for input
read -p "Do you want to proceed? (yes/no): " response

# Convert the response to lowercase
response=$(echo "$response" | tr '[:upper:]' '[:lower:]')

# Check the user's response
if [[ "$response" == "yes" ]]; then
    echo "You chose yes. Proceeding..."
    uv run pyright -p pyproject.toml . | grep "Stub file not found for" | sed -n 's/.*Stub file not found for "\([^"]*\)".*/\1/p' | sort | uniq | xargs -I {} uv run pyright --createstub {}
    # Add the commands you want to execute if the user says yes
elif [[ "$response" == "no" ]]; then
    echo "You chose no. Exiting..."
    # Add the commands you want to execute if the user says no
else
    echo "Invalid input. Please enter yes or no."
    # Optionally, you can loop back and ask the user again
fi

# Example commands generated
# pyright --createstub better_exceptions
# pyright --createstub bpdb
# pyright --createstub pinecone
# pyright --createstub discord
# pyright --createstub transformers
# pyright --createstub uritools
# pyright --createstub torchvision
# pyright --createstub scipy
# pyright --createstub webcolors
# pyright --createstub logging_tree

echo 'Typing stub generation completed'

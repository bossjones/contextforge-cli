#!/bin/bash
# Shebang line specifying that this is a bash script

# uv pip compile pyproject.toml --python-version 3.12 --python-platform linux - -o contextforge_cli/requirements-linux.txt --upgrade
# This line is commented out, but it would compile requirements for Linux using uv

# Export base requirements
# uv export --no-hashes --prune langserve --prune notebook --format requirements-txt --extra dev  -o contextforge_cli/requirements.txt
# This line is commented out, but it would export requirements including dev dependencies

# Export base requirements without dev dependencies
uv export --no-dev --no-hashes --prune langserve --prune notebook --format requirements-txt -o contextforge_cli/requirements.txt

# Check if yq is installed, exit with an error message if not
command -v yq >/dev/null 2>&1 || { echo >&2 "yq is required but it's not installed. run 'brew install yq' or 'pip install yq'"; exit 1; }

# Check if langgraph is installed, exit with an error message if not
command -v langgraph >/dev/null 2>&1 || { echo >&2 "langgraph is required but it's not installed. run 'brew install langgraph-cli' or 'pip install langgraph-cli'"; exit 1; }

# Get all dependencies from pyproject.toml and process them
yq -r ".project.dependencies[]" pyproject.toml | while read -r dep; do
    # Extract package name
    pkg=$(echo "$dep" | gsed -E "s/([^>=<~!]+).*/\1/")
    # Extract version specifier
    ver=$(echo "$dep" | gsed -E "s/[^>=<~!]+(.+)/\1/")
    # Update the package in requirements.txt with the version from pyproject.toml
    gsed -i "s|^$pkg==.*|$pkg$ver|g" contextforge_cli/requirements.txt
done

# Get all dev-dependencies and process them
yq -r ".[\"tool.uv\"][\"dev-dependencies\"][]" pyproject.toml | while read -r dep; do
    # Extract package name
    pkg=$(echo "$dep" | gsed -E "s/([^>=<~!]+).*/\1/")
    # Extract version specifier
    ver=$(echo "$dep" | gsed -E "s/[^>=<~!]+(.+)/\1/")
    # Update the package in requirements.txt with the version from pyproject.toml
    gsed -i "s|^$pkg==.*|$pkg$ver|g" contextforge_cli/requirements.txt
done

# Remove exact version requirement for sse-starlette
gsed -i 's/^sse-starlette==.*/sse-starlette/g' contextforge_cli/requirements.txt

# Remove exact version requirements for langserve[all], langserve, and tenacity
gsed -i 's/^langserve\[all\]==.*/langserve\[all\]/g' contextforge_cli/requirements.txt
gsed -i 's/^langserve==.*/langserve/g' contextforge_cli/requirements.txt
gsed -i 's/^tenacity==.*/tenacity/g' contextforge_cli/requirements.txt

gsed -i 's/^langgraph-sdk==.*/langgraph-sdk/g' contextforge_cli/requirements.txt
gsed -i 's/^langgraph==.*/langgraph/g' contextforge_cli/requirements.txt

# Show the changes made to requirements.txt
# git diff contextforge_cli/requirements.txt

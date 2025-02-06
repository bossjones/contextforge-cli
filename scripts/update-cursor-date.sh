#!/usr/bin/env bash

# Path to the .cursor-updates file (update this with your own .cursor-updates file)
CURSOR_FILE="~/dev/bossjones/contextforge-cli/.cursor-updates"

# Get today's date in YYYY-MM-DD format
TODAY=$(date +%Y-%m-%d)

# Create a temporary file
TMP_FILE=$(mktemp)

# Write the new date line
echo "## ${TODAY}" > "$TMP_FILE"

# Append the rest of the file starting from line 4 (skipping the header and old date)
tail -n +4 "$CURSOR_FILE" >> "$TMP_FILE"

# Add the header back with today's date
(
  echo "# Cursor Updates"
  echo ""
  echo "This file tracks significant changes made to the codebase through Cursor agent interactions. Today's date is: ${TODAY}"
  cat "$TMP_FILE"
) > "$CURSOR_FILE"

# Clean up
rm "$TMP_FILE"

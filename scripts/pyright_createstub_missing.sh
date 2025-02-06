	#!/usr/bin/env zsh
	# Run pyright and capture output
	uv run pyright . | grep -E "warning: Stub file not found for \"[^\"]+\"" | sed -E 's/.*"([^"]+)".*/\1/' | sort -u | while read package; do
		echo "Creating stub for package: $package"
		uv run pyright --createstub "$package"
	done

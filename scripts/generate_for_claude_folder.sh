#!/usr/bin/env zsh

# Color setup for the terminal
setup_colors() {
    # Only setup colors if connected to a terminal
    if [ -t 1 ]; then
        # Reset
        RESET='\033[0m'

        # Regular Colors
        GREEN='\033[0;32m'
        YELLOW='\033[0;33m'
        RED='\033[0;31m'
        BLUE='\033[0;34m'
        CYAN='\033[0;36m'

        # Bold Colors
        BOLD_GREEN='\033[1;32m'
        BOLD_YELLOW='\033[1;33m'
        BOLD_RED='\033[1;31m'
        BOLD_BLUE='\033[1;34m'
        BOLD_CYAN='\033[1;36m'
    else
        # No colors if not in a terminal
        RESET=''
        GREEN=''
        YELLOW=''
        RED=''
        BLUE=''
        CYAN=''
        BOLD_GREEN=''
        BOLD_YELLOW=''
        BOLD_RED=''
        BOLD_BLUE=''
        BOLD_CYAN=''
    fi
}

# Initialize colors
setup_colors

# Logging functions
log_info() {
    printf "${GREEN}[INFO]${RESET} %s\n" "$*" >&2
}

log_success() {
    printf "${BOLD_GREEN}[SUCCESS]${RESET} %s\n" "$*" >&2
}

log_warn() {
    printf "${YELLOW}[WARNING]${RESET} %s\n" "$*" >&2
}

log_error() {
    printf "${BOLD_RED}[ERROR]${RESET} %s\n" "$*" >&2
}

log_prompt() {
    printf "${BOLD_BLUE}[PROMPT]${RESET} %s\n" "$*" >&2
}

log_cmd() {
    printf "${CYAN}[CMD]${RESET} %s\n" "$*" >&2
}

log_debug() {
    printf "${BLUE}[DEBUG]${RESET} %s\n" "$*" >&2
}

# Initialize counters
total_files=0
processed_files=0
failed_files=0
skipped_files=0

# Get start time
start_time=$SECONDS

# Check if directories were provided
if [ $# -lt 1 ]; then
    log_error "No directories provided"
    log_prompt "Usage: $0 dir1 [dir2 ...]"
    log_prompt "Example: $0 ./contextforge_cli ./tests"
    exit 1
fi

# Create the base output directory
log_info "Creating output directory: ai_docs/for_claude"
mkdir -p ai_docs/for_claude || true

# Process each provided directory
for dir in "$@"; do
    if [ ! -d "$dir" ]; then
        log_warn "$dir is not a directory, skipping..."
        continue
    fi

    log_info "Processing directory: $dir"

    # Count total files before processing
    dir_files=($dir/**/*(.))
    dir_file_count=${#dir_files[@]}
    total_files=$((total_files + dir_file_count))
    log_info "Found $dir_file_count files in $dir"

    # Process files directly in zsh without using find
    for file in $dir/**/*(.); do
        # Skip hidden files and directories
        if [[ $file == .* ]]; then
            log_debug "Skipping hidden file: $file"
            skipped_files=$((skipped_files + 1))
            continue
        fi

        # Create the output directory structure
        dir_path=${file:h}
        output_dir="ai_docs/for_claude/$dir_path"
        mkdir -p "$output_dir"

        # Generate output filename
        base_name=${file:t}
        output_file="$output_dir/$base_name.xml"

        # Calculate progress percentage
        progress=$((processed_files * 100 / total_files))
        elapsed=$((SECONDS - start_time))

        log_info "[$progress%] Processing file $((processed_files + 1))/$total_files: $file -> $output_file (${elapsed}s elapsed)"

        if uv run files-to-prompt "$file" --cxml -o "$output_file"; then
            log_success "Successfully processed $file"
            processed_files=$((processed_files + 1))
        else
            log_error "Failed to process $file"
            failed_files=$((failed_files + 1))
        fi

        # Log intermediate statistics every 10 files
        if (( processed_files % 10 == 0 )); then
            log_info "Progress update:"
            log_info "  - Processed: $processed_files"
            log_info "  - Failed: $failed_files"
            log_info "  - Skipped: $skipped_files"
            log_info "  - Remaining: $((total_files - processed_files - failed_files - skipped_files))"
            log_info "  - Time elapsed: ${elapsed}s"
        fi
    done
done

# Calculate final statistics
end_time=$SECONDS
duration=$((end_time - start_time))
success_rate=$(( (processed_files * 100) / total_files ))

# Log final summary
log_success "Processing complete!"
log_info "Final Statistics:"
log_info "  - Total files found: $total_files"
log_info "  - Successfully processed: $processed_files"
log_info "  - Failed: $failed_files"
log_info "  - Skipped: $skipped_files"
log_info "  - Success rate: ${success_rate}%"
log_info "  - Total time: ${duration}s"

# Example usage:
#
# Process the contextforge-cli codebase and tests:
#   ./generate_for_claude_folder.sh /Users/malcolm/dev/bossjones/contextforge-cli-main/contextforge_cli /Users/malcolm/dev/bossjones/contextforge-cli-main/tests
#
# This will create:
#   ai_docs/for_claude/Users/malcolm/dev/bossjones/contextforge-cli-main/contextforge_cli/*.xml
#   ai_docs/for_claude/Users/malcolm/dev/bossjones/contextforge-cli-main/tests/*.xml
#
# You can also use relative paths if you're in the contextforge-cli-main directory:
#   ./generate_for_claude_folder.sh ./contextforge_cli ./tests
